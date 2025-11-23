import os
import logging
import asyncio
import re
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request
from typing import Optional, List
from .models import AgentDeployResponse
from database.supabase.operations import AgentsOperations, ProductsOperations
from database.supabase.client import get_supabase_client
from utils.wallet import create_wallet, encrypt_pk, send_eth_to_wallet
from utils.chaoschain import create_chaoschain_agent
from utils.image_upload import upload_product_image
from chaoschain_sdk import AgentRole

router = APIRouter(prefix="/agent", tags=["agent"])
logger = logging.getLogger(__name__)


async def upload_image_to_supabase(image_file: UploadFile, agent_id: str, bucket_name: str = "agents") -> str:
    """
    Upload image to Supabase Storage and return public URL.
    
    Args:
        image_file: UploadFile from FastAPI
        agent_id: UUID of the agent for folder organization
        bucket_name: Name of the Supabase storage bucket
    
    Returns:
        Public URL for the uploaded image
    """
    try:
        client = get_supabase_client()
        
        # Use original filename or default
        filename = image_file.filename or "image.png"
        file_path = f"images/{agent_id}/{filename}"
        
        # Read file content with size validation (max 10MB)
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
        file_content = await image_file.read()
        
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024 * 1024):.1f}MB"
            )
        
        content_type = image_file.content_type or "image/png"
        
        logger.info(f"Uploading image to Supabase Storage: {file_path} ({len(file_content)} bytes)")
        
        # Run synchronous Supabase operations in a thread pool to avoid blocking
        # This also helps with timeout handling
        def upload_file():
            """Synchronous upload function to run in thread pool"""
            storage_response = client.storage.from_(bucket_name).upload(
                file_path,
                file_content,
                file_options={"content-type": content_type, "upsert": "false"}
            )
            return storage_response
        
        def get_public_url():
            """Synchronous public URL retrieval to run in thread pool"""
            return client.storage.from_(bucket_name).get_public_url(file_path)
        
        # Upload to Supabase Storage (run in thread pool with timeout)
        upload_succeeded = False
        upload_exception = None
        
        try:
            storage_response = await asyncio.wait_for(
                asyncio.to_thread(upload_file),
                timeout=300.0  # 5 minutes timeout
            )
            
            if storage_response:
                logger.info(f"Image uploaded to Supabase Storage: {file_path}")
                upload_succeeded = True
        except asyncio.TimeoutError as e:
            # Upload might have succeeded but response timed out
            # This is common - the file uploads but we don't get the response
            upload_exception = e
            logger.warning(
                f"Upload response timed out for: {file_path}. "
                f"This may mean the upload succeeded but the response was slow. "
                f"Will attempt to retrieve URL anyway."
            )
            # Wait a moment for upload to complete server-side
            await asyncio.sleep(2)
        except Exception as e:
            # Other exceptions - log but still try to get URL in case upload succeeded
            upload_exception = e
            logger.warning(f"Exception during upload for: {file_path}: {str(e)}. Will attempt to retrieve URL anyway.")
            await asyncio.sleep(2)
        
        # If upload didn't succeed normally, try to verify by getting the URL
        # If we can get a URL, the upload likely succeeded
        verified_public_url = None
        if not upload_succeeded and upload_exception:
            logger.info(f"Attempting to verify upload by retrieving URL for: {file_path}")
            try:
                # Try to get public URL - if upload succeeded, this will work
                verified_public_url = await asyncio.wait_for(
                    asyncio.to_thread(get_public_url),
                    timeout=15.0
                )
                if verified_public_url:
                    logger.info(f"✓ File is accessible via public URL. Upload succeeded despite timeout.")
                    upload_succeeded = True
            except Exception as e:
                logger.warning(f"Could not retrieve URL to verify upload: {str(e)}")
        
        # Only fail if we're certain the upload didn't work
        if not upload_succeeded:
            error_msg = "Upload operation timed out or failed."
            if upload_exception:
                if isinstance(upload_exception, asyncio.TimeoutError):
                    error_msg += " Please try again with a smaller file."
                else:
                    error_msg += " The file may have been uploaded successfully. Please check Supabase storage."
            logger.error(f"Upload failed for: {file_path}")
            raise HTTPException(
                status_code=504,
                detail=error_msg
            )
        
        # Return public URL (not signed URL) for direct access
        # Use verified_public_url if we already have it from timeout recovery
        if verified_public_url:
            logger.info(f"Using verified public URL for: {file_path}")
            return verified_public_url
        
        # Get public URL
        try:
            public_url = await asyncio.wait_for(
                asyncio.to_thread(get_public_url),
                timeout=30.0
            )
            logger.info(f"Using public URL for: {file_path}")
            return public_url
        except Exception as e:
            logger.error(f"Failed to get public URL: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve file URL: {str(e)}"
            )
        
    except HTTPException:
        raise
    except asyncio.TimeoutError as e:
        logger.error(f"Timeout error uploading image to Supabase: {str(e)}")
        raise HTTPException(
            status_code=504,
            detail="Upload operation timed out. Please try again with a smaller file or check your network connection."
        )
    except Exception as e:
        logger.error(f"Error uploading image to Supabase: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload image: {str(e)}"
        )


@router.post("/deploy-agent", response_model=AgentDeployResponse)
async def deploy_agent(
    request: Request,
    agent_type: str = Form(...),
    name: str = Form(...),
    domain: str = Form(...),
    image: Optional[UploadFile] = File(None),
    preset_avatar: Optional[str] = Form(None),
    category: Optional[str] = Form(None),  # Merchant category: TECH, FASHION, etc.
    description: Optional[str] = Form(None),
    products_json: Optional[str] = Form(None),
    search_items_json: Optional[str] = Form(None),
    owner: Optional[str] = Form(None),
    user_wallet_address: Optional[str] = Form(None),  # Privy user wallet
    user_id: Optional[str] = Form(None),  # Privy user ID
    # ChaosChain configuration options
    agent_role: Optional[str] = Form(None),
    enable_payments: Optional[str] = Form(None),
    enable_process_integrity: Optional[str] = Form(None),
    enable_ap2: Optional[str] = Form(None)
):
    """
    Create an agent in Supabase and upload image if provided.
    Also handles product images (up to 3 per product).
    
    Accepts form data with optional image file upload and ChaosChain configuration.
    
    Product images are sent as: product_0_image_0, product_0_image_1, etc.
    
    ChaosChain Options:
    - agent_role: Optional. One of: "SERVER", "CLIENT", "VALIDATOR", "WORKER", "VERIFIER", "ORCHESTRATOR". Default: "SERVER"
    - enable_payments: Optional. "true" or "false". Default: "true"
    - enable_process_integrity: Optional. "true" or "false". Default: "true"
    - enable_ap2: Optional. "true" or "false". Default: "true"
    """
    try:
        # Validate inputs
        if not name or not name.strip():
            raise HTTPException(
                status_code=400,
                detail="Agent name cannot be empty"
            )
        
        if not agent_type or not agent_type.strip():
            raise HTTPException(
                status_code=400,
                detail="Agent type cannot be empty"
            )
        
        # Validate agent_type is either "client" or "merchant"
        agent_type_lower = agent_type.strip().lower()
        if agent_type_lower not in ["client", "merchant"]:
            raise HTTPException(
                status_code=400,
                detail="Agent type must be either 'client' or 'merchant'"
            )
        
        # Create wallet for the agent
        logger.info("Creating wallet for agent...")
        wallet = await asyncio.to_thread(create_wallet)
        logger.info(f"Wallet created: {wallet['address']}")
        
        # Fund the agent wallet from admin wallet
        creation_gas_fee = os.getenv("CREATION_GAS_FEE")
        admin_private_key = os.getenv("ADMIN_PRIVATE_KEY")
        
        if creation_gas_fee and admin_private_key:
            try:
                logger.info(f"Funding agent wallet with {creation_gas_fee} ETH from admin wallet...")
                funding_result = await asyncio.to_thread(
                    send_eth_to_wallet,
                    recipient_address=wallet["address"],
                    amount_eth=creation_gas_fee,
                    admin_private_key=admin_private_key
                )
                logger.info(
                    f"✓ Agent wallet funded successfully. "
                    f"Transaction: {funding_result['transaction_hash']}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to fund agent wallet: {str(e)}. "
                    f"Agent creation will continue, but registration may fail if wallet has insufficient funds."
                )
                # Continue with agent creation even if funding fails
                # The user can manually fund the wallet later
        else:
            if not creation_gas_fee:
                logger.warning(
                    "CREATION_GAS_FEE not set in environment. "
                    "Agent wallet will not be automatically funded."
                )
            if not admin_private_key:
                logger.warning(
                    "ADMIN_PRIVATE_KEY not set in environment. "
                    "Agent wallet will not be automatically funded."
                )
        
        # Parse ChaosChain configuration options
        # Agent role
        parsed_agent_role = AgentRole.SERVER  # Default
        if agent_role:
            agent_role_upper = agent_role.strip().upper()
            try:
                # Try to get the enum value (handles SERVER, CLIENT, WORKER, VERIFIER, ORCHESTRATOR, etc.)
                parsed_agent_role = getattr(AgentRole, agent_role_upper, AgentRole.SERVER)
            except (AttributeError, TypeError):
                logger.warning(f"Invalid agent_role '{agent_role}', using default SERVER")
                parsed_agent_role = AgentRole.SERVER
        
        # Boolean flags (parse string "true"/"false" to boolean)
        def parse_bool(value: Optional[str], default: bool = True) -> bool:
            if value is None:
                return default
            value_lower = value.strip().lower()
            if value_lower in ("true", "1", "yes", "on"):
                return True
            elif value_lower in ("false", "0", "no", "off"):
                return False
            return default
        
        enable_payments_bool = parse_bool(enable_payments, default=True)
        enable_process_integrity_bool = parse_bool(enable_process_integrity, default=True)
        enable_ap2_bool = parse_bool(enable_ap2, default=True)
        
        # Create and register ChaosChain agent
        logger.info("Registering ChaosChain agent...")
        agent_domain = str(domain).strip() if domain else f"{str(name).strip().lower().replace(' ', '-')}.mydomain.com"
        chaoschain_result = await asyncio.to_thread(
            create_chaoschain_agent,
            agent_name=str(name).strip(),
            agent_domain=agent_domain,
            private_key=wallet["private_key"],
            agent_role=parsed_agent_role,
            enable_payments=enable_payments_bool,
            enable_process_integrity=enable_process_integrity_bool,
            enable_ap2=enable_ap2_bool
        )
        logger.info(f"ChaosChain agent registered: {chaoschain_result['agent_id']}")
        
        # Encrypt private key
        logger.info("Encrypting private key...")
        encrypted_private_key = await asyncio.to_thread(
            encrypt_pk,
            wallet["private_key"]
        )
        logger.info("Private key encrypted successfully")
        
        # Create agent record in Supabase
        logger.info("Creating agent record in Supabase...")
        agents_ops = AgentsOperations()
        products_ops = ProductsOperations()
        
        # Parse products/search items JSON if provided
        products_data = None
        search_items_data = None
        
        if products_json:
            try:
                import json
                products_data = json.loads(products_json)
            except Exception as e:
                logger.warning(f"Failed to parse products_json: {str(e)}")
        
        if search_items_json:
            try:
                import json
                search_items_data = json.loads(search_items_json)
            except Exception as e:
                logger.warning(f"Failed to parse search_items_json: {str(e)}")
        
        # Prepare metadata for the agent (including ChaosChain config)
        # Note: metadata column doesn't exist in current schema, we'll use products table instead
        
        # Determine owner: use provided owner, or wallet address, or user_id
        agent_owner = owner.strip() if owner else (user_wallet_address or user_id)
        
        agent_record = agents_ops.create_agent(
            chaoschain_agent_id=chaoschain_result["agent_id"],
            transaction_hash=chaoschain_result["transaction_hash"],
            public_address=chaoschain_result["public_address"],
            encrypted_private_key=encrypted_private_key,
            agent_type=agent_type_lower,
            name=str(name).strip(),
            owner=agent_owner,
            category=category if agent_type_lower == "merchant" else None
        )
        db_agent_id = agent_record["id"]
        
        logger.info(f"Created agent record with ID: {db_agent_id}")
        
        # Upload avatar image to Supabase Storage if provided
        avatar_url = None
        if image:
            logger.info("Uploading custom avatar to Supabase Storage...")
            avatar_url = await upload_image_to_supabase(image, str(db_agent_id))
            logger.info(f"Avatar uploaded successfully: {avatar_url}")
            
            # Update agent record with avatar URL
            agents_ops.update_agent_avatar_url(
                agent_id=db_agent_id,
                avatar_url=avatar_url
            )
        elif preset_avatar:
            # Use preset avatar emoji as avatar_url
            logger.info(f"Using preset avatar: {preset_avatar}")
            agents_ops.update_agent_avatar_url(
                agent_id=db_agent_id,
                avatar_url=preset_avatar  # Store emoji directly
            )
            avatar_url = preset_avatar
        
        # Insert products into products table if merchant
        if agent_type_lower == "merchant" and products_data:
            logger.info(f"Inserting {len(products_data)} products for merchant agent {db_agent_id}")
            try:
                # Get form data to extract product images
                form_data = await request.form()
                
                # Create products
                created_products = []
                for idx, product in enumerate(products_data):
                    # Try to get image for this product (product_image_0, product_image_1, etc.)
                    image_key = f"product_image_{idx}"
                    product_image_urls = []
                    
                    if image_key in form_data:
                        image_file = form_data[image_key]
                        if isinstance(image_file, UploadFile) and image_file.filename:
                            logger.info(f"Found image for product {idx}: {image_file.filename}")
                            
                            # Upload image to Supabase Storage
                            image_url = await upload_product_image(
                                image_file,
                                str(db_agent_id),
                                idx
                            )
                            
                            if image_url:
                                product_image_urls.append(image_url)
                                logger.info(f"✓ Product {idx} image uploaded: {image_url}")
                            else:
                                logger.warning(f"Failed to upload image for product {idx}")
                    
                    # Insert product into database
                    created_product = products_ops.create_product(
                        agent_id=db_agent_id,
                        name=product["name"],
                        price=str(product["price"]),
                        stock=product["stock"],
                        negotiation_percentage=product.get("maxDiscount", 0),
                        images=product_image_urls  # Pass image URLs array
                    )
                    created_products.append(created_product)
                    logger.info(f"✓ Product '{product['name']}' created with {len(product_image_urls)} image(s)")
                
                logger.info(f"✓ Successfully inserted {len(created_products)} products")
            except Exception as e:
                logger.error(f"Failed to insert products: {str(e)}")
                # Don't fail the whole deployment if products insert fails
                # Agent is already created, products can be added later
        
        logger.info(
            f"Agent created successfully. "
            f"DB ID: {db_agent_id}, "
            f"Name: {name}, "
            f"Type: {agent_type_lower}"
        )
        
        # Return response with all agent details
        response_metadata = {
            "name": str(name).strip(),
            "type": agent_type_lower,
            "agent_id": chaoschain_result["agent_id"],
            "public_address": chaoschain_result["public_address"],
            "transaction_hash": chaoschain_result["transaction_hash"]
        }
        if owner:
            response_metadata["owner"] = owner.strip()
        if user_wallet_address:
            response_metadata["user_wallet_address"] = user_wallet_address
        if user_id:
            response_metadata["user_id"] = user_id
        
        return AgentDeployResponse(
            agent_id=str(db_agent_id),
            db_id=str(db_agent_id),  # Same as agent_id, this is the Supabase UUID
            status="created",
            agent0_id=None,
            metadata=response_metadata,
            avatar_url=avatar_url
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent creation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/my-agents")
async def get_my_agents(owner: str):
    """
    Get all agents owned by a specific user.
    
    Args:
        owner: Owner wallet address or Privy user ID
    
    Returns:
        List of agents with product counts
    """
    try:
        agents_ops = AgentsOperations()
        agents = agents_ops.get_agents_by_owner(owner)
        
        # Enrich with product counts
        from database.supabase.operations import ProductsOperations
        products_ops = ProductsOperations()
        
        enriched_agents = []
        for agent in agents:
            # Get product count for this agent
            try:
                products = products_ops.get_products_by_agent(agent["id"])
                product_count = len(products)
            except Exception as e:
                logger.warning(f"Failed to get products for agent {agent['id']}: {str(e)}")
                product_count = 0
            
            enriched_agents.append({
                **agent,
                "products_count": product_count
            })
        
        return {"agents": enriched_agents}
        
    except Exception as e:
        logger.error(f"Failed to get user agents: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/list")
async def list_live_agents():
    """
    Get all live agents for market display.
    Only returns merchant agents with status='live'.
    
    Returns:
        List of live agents with product counts
    """
    try:
        agents_ops = AgentsOperations()
        agents = agents_ops.get_live_agents()
        
        # Enrich with product counts
        from database.supabase.operations import ProductsOperations
        products_ops = ProductsOperations()
        
        enriched_agents = []
        for agent in agents:
            # Get product count for this agent
            try:
                products = products_ops.get_products_by_agent(agent["id"])
                product_count = len(products)
            except Exception as e:
                logger.warning(f"Failed to get products for agent {agent['id']}: {str(e)}")
                product_count = 0
            
            enriched_agents.append({
                **agent,
                "products_count": product_count
            })
        
        return {"agents": enriched_agents}
        
    except Exception as e:
        logger.error(f"Failed to get live agents: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{agent_id}")
async def get_agent(agent_id: str):
    """
    Get single agent details by ID.
    
    Args:
        agent_id: UUID of the agent
    
    Returns:
        Agent record with product count
    """
    try:
        from uuid import UUID
        agents_ops = AgentsOperations()
        agent = agents_ops.get_agent_by_id(UUID(agent_id))
        
        if not agent:
            raise HTTPException(
                status_code=404,
                detail=f"Agent {agent_id} not found"
            )
        
        # Get product count
        from database.supabase.operations import ProductsOperations
        products_ops = ProductsOperations()
        try:
            products = products_ops.get_products_by_agent(agent_id)
            product_count = len(products)
        except Exception as e:
            logger.warning(f"Failed to get products for agent {agent_id}: {str(e)}")
            product_count = 0
        
        return {
            **agent,
            "products_count": product_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{agent_id}/products")
async def get_agent_products(agent_id: str):
    """
    Get all products for a specific agent.
    
    Args:
        agent_id: UUID of the agent
    
    Returns:
        List of products
    """
    try:
        from database.supabase.operations import ProductsOperations
        products_ops = ProductsOperations()
        
        products = products_ops.get_products_by_agent(agent_id)
        
        return {"products": products}
        
    except Exception as e:
        logger.error(f"Failed to get agent products: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.patch("/{agent_id}/status")
async def update_agent_status(agent_id: str, status: str):
    """
    Update agent status (live, paused, draft).
    
    Args:
        agent_id: UUID of the agent
        status: New status ('live', 'paused', or 'draft')
    
    Returns:
        Updated agent record
    """
    try:
        from uuid import UUID
        
        if status not in ["live", "paused", "draft"]:
            raise HTTPException(
                status_code=400,
                detail="Status must be 'live', 'paused', or 'draft'"
            )
        
        agents_ops = AgentsOperations()
        updated_agent = agents_ops.update_agent_status(UUID(agent_id), status)
        
        return updated_agent
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update agent status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


