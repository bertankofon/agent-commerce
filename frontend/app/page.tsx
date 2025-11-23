"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { usePrivy } from '@privy-io/react-auth';

export default function Home() {
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const { ready, authenticated, login, user } = usePrivy();

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
              <p className="text-cyan-300/70 text-lg mb-2">Autonomous AI Agents</p>
              <p className="text-cyan-300/50 text-lg">Trading on Blockchain</p>
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
                  <span className="relative z-10">CONNECT WALLET</span>
                  <div className="absolute inset-0 bg-cyan-400/5 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"></div>
                </button>
              ) : (
                <>
                  <Link
                    href="/deploy"
                    className="group relative px-20 py-5 border-2 border-cyan-400/60 rounded-full text-cyan-400 font-bold text-lg hover:border-cyan-400 transition-all duration-300 neon-button overflow-hidden"
                  >
                    <span className="relative z-10">DEPLOY AGENT</span>
                    <div className="absolute inset-0 bg-cyan-400/5 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"></div>
                  </Link>
                  {user?.wallet?.address && (
                    <p className="text-cyan-400/60 text-sm">
                      {user.wallet.address.slice(0, 6)}...{user.wallet.address.slice(-4)}
                    </p>
                  )}
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
