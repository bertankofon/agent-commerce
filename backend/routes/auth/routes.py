import logging
from fastapi import APIRouter, HTTPException
from .models import UserLoginRequest, UserResponse
from database.supabase.operations import UsersOperations

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


@router.post("/login-or-register", response_model=UserResponse)
async def login_or_register_user(request: UserLoginRequest):
    """
    Login or register a user with Privy credentials.
    
    This endpoint should be called after Privy authentication succeeds.
    It will create a new user if they don't exist, or return existing user data.
    
    Args:
        request: User login request with Privy data
    
    Returns:
        User record from database
    """
    try:
        # Validate user_type
        if request.user_type not in ["merchant", "client"]:
            raise HTTPException(
                status_code=400,
                detail="user_type must be either 'merchant' or 'client'"
            )
        
        users_ops = UsersOperations()
        
        # Create or update user
        user_record = users_ops.create_or_update_user(
            privy_user_id=request.privy_user_id,
            wallet_address=request.wallet_address,
            user_type=request.user_type,
            email=request.email,
            name=request.name
        )
        
        logger.info(
            f"User logged in/registered: {user_record['id']}, "
            f"Privy ID: {request.privy_user_id}, "
            f"Type: {request.user_type}"
        )
        
        return UserResponse(
            id=user_record["id"],
            privy_user_id=user_record["privy_user_id"],
            wallet_address=user_record["wallet_address"],
            user_type=user_record["user_type"],
            email=user_record.get("email"),
            name=user_record.get("name"),
            created_at=user_record["created_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User login/registration failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/user/{privy_user_id}", response_model=UserResponse)
async def get_user_by_privy_id(privy_user_id: str):
    """
    Get user by Privy user ID.
    
    Args:
        privy_user_id: Privy user ID
    
    Returns:
        User record from database
    """
    try:
        users_ops = UsersOperations()
        user_record = users_ops.get_user_by_privy_id(privy_user_id)
        
        if not user_record:
            raise HTTPException(
                status_code=404,
                detail=f"User with Privy ID {privy_user_id} not found"
            )
        
        return UserResponse(
            id=user_record["id"],
            privy_user_id=user_record["privy_user_id"],
            wallet_address=user_record["wallet_address"],
            user_type=user_record["user_type"],
            email=user_record.get("email"),
            name=user_record.get("name"),
            created_at=user_record["created_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

