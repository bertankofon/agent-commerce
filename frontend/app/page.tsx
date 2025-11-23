"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { usePrivy } from '@privy-io/react-auth';
import { loginOrRegisterUser } from './lib/auth';
import WalletButton from './components/WalletButton';

export default function Home() {
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [isRegistering, setIsRegistering] = useState(false);
  const { ready, authenticated, login, user } = usePrivy();

  // Auto-register/login user when authenticated
  useEffect(() => {
    const registerUser = async () => {
      if (authenticated && user && !isRegistering) {
        try {
          setIsRegistering(true);
          
          // Get user data from Privy
          const privyUserId = user.id;
          const walletAddress = user.wallet?.address;
          
          if (!walletAddress) {
            console.error('No wallet address found');
            return;
          }
          
          // Extract email and name from Privy user object
          const email = user.email?.address || user.google?.email || undefined;
          const name = user.google?.name || undefined;
          
          // Register or login user to backend
          await loginOrRegisterUser({
            privy_user_id: privyUserId,
            wallet_address: walletAddress,
            email,
            name,
          });
          
          console.log('User registered/logged in successfully');
        } catch (error) {
          console.error('Failed to register/login user:', error);
        } finally {
          setIsRegistering(false);
        }
      }
    };
    
    registerUser();
  }, [authenticated, user, isRegistering]);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      const x = (e.clientX / window.innerWidth - 0.5) * 2;
      const y = (e.clientY / window.innerHeight - 0.5) * 2;
      setMousePos({ x, y });
    };

    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  return (
    <div className="min-h-screen bg-black relative overflow-hidden">
      {/* Wallet Button - Top Right */}
      <WalletButton />
      
      {/* Space Background */}
      <div 
        className="space-bg"
        style={{
          transform: `translate(${mousePos.x * 10}px, ${mousePos.y * 10}px)`,
          transition: 'transform 0.3s ease-out'
        }}
      >
        <div className="perspective-grid"></div>
        <div className="stars"></div>
        <div 
          className="floating-orb orb-1"
          style={{
            transform: `translate(${mousePos.x * 30}px, ${mousePos.y * 30}px)`,
            transition: 'transform 0.5s ease-out'
          }}
        ></div>
        <div 
          className="floating-orb orb-2"
          style={{
            transform: `translate(${-mousePos.x * 40}px, ${-mousePos.y * 40}px)`,
            transition: 'transform 0.5s ease-out'
          }}
        ></div>
      </div>

      {/* Content */}
      <div className="relative z-10 flex items-center justify-center min-h-screen p-8">
        <div className="max-w-3xl w-full">
          {/* Main Container */}
          <div 
            className="border border-cyan-400/20 rounded-3xl p-16 backdrop-blur-sm bg-black/50"
            style={{
              transform: `perspective(1000px) rotateY(${mousePos.x * 3}deg) rotateX(${-mousePos.y * 3}deg)`,
              transition: 'transform 0.3s ease-out'
            }}
          >
            {/* Title */}
            <div className="text-center mb-16">
              <h1 className="text-8xl font-bold mb-8 tracking-wider neon-text">
                EPOCH
              </h1>
              <div className="h-px w-32 bg-gradient-to-r from-transparent via-cyan-400/50 to-transparent mx-auto mb-8"></div>
              <p className="text-cyan-300/70 text-xl italic font-bold">Economies evolve when humans step aside</p>
            </div>

            {/* Enter Button */}
            <div className="flex flex-col items-center gap-4">
              {!ready ? (
                <div className="px-20 py-5 border-2 border-cyan-400/30 rounded-full text-cyan-400/50 font-bold text-lg">
                  LOADING...
                </div>
              ) : !authenticated ? (
                <button
                  onClick={login}
                  className="group relative px-20 py-5 border-2 border-cyan-400/60 rounded-full text-cyan-400 font-bold text-lg hover:border-cyan-400 transition-all duration-300 neon-button overflow-hidden"
                >
                  <span className="relative z-10">CONNECT</span>
                  <div className="absolute inset-0 bg-cyan-400/5 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"></div>
                </button>
              ) : (
                <>
                  <div className="flex gap-4">
                    <Link
                      href="/deploy"
                      className="group relative px-12 py-5 border-2 border-cyan-400/60 rounded-full text-cyan-400 font-bold text-lg hover:border-cyan-400 transition-all duration-300 neon-button overflow-hidden"
                    >
                      <span className="relative z-10">DEPLOY AGENT</span>
                      <div className="absolute inset-0 bg-cyan-400/5 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"></div>
                    </Link>
                    <Link
                      href="/market"
                      className="group relative px-12 py-5 border-2 border-cyan-400/60 rounded-full text-cyan-400 font-bold text-lg hover:border-cyan-400 transition-all duration-300 neon-button overflow-hidden"
                    >
                      <span className="relative z-10">MARKET</span>
                      <div className="absolute inset-0 bg-cyan-400/5 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"></div>
                    </Link>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Footer */}
          <div className="text-center mt-8">
            <p className="text-cyan-400/30 text-sm">Powered by ChaosChain</p>
          </div>
        </div>
      </div>
    </div>
  );
}
