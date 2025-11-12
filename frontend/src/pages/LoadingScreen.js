import { useState, useEffect } from "react";
import { Brain, Sparkles, ChartNoAxesColumn, Rocket } from "lucide-react";

const LoadingScreen = () => {
  const [currentMessage, setCurrentMessage] = useState(0);

  const messages = [
    "Parsing your resume...",
    "Extracting your unique skills...",
    "Analyzing job market trends...",
    "Calculating skill-gap analysis...",
    "Building your career roadmap...",
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentMessage((prev) => (prev + 1) % messages.length);
    }, 1500);

    return () => clearInterval(interval);
  }, []);

  return (
    <div
      className="min-h-screen flex items-center justify-center"
      style={{ background: 'linear-gradient(135deg, #e0f2f1 0%, #b2dfdb 50%, #80cbc4 100%)' }}
    >
      <div className="text-center">
        {/* Animated Network Graph */}
        <div className="relative w-64 h-64 mx-auto mb-8">
          <svg className="w-full h-full" viewBox="0 0 200 200">
            {/* Nodes */}
            <circle
              cx="100"
              cy="30"
              r="8"
              fill="#00897b"
              className="animate-pulse"
              style={{ animationDelay: '0s' }}
            />
            <circle
              cx="170"
              cy="80"
              r="8"
              fill="#00897b"
              className="animate-pulse"
              style={{ animationDelay: '0.2s' }}
            />
            <circle
              cx="150"
              cy="150"
              r="8"
              fill="#00897b"
              className="animate-pulse"
              style={{ animationDelay: '0.4s' }}
            />
            <circle
              cx="50"
              cy="150"
              r="8"
              fill="#00897b"
              className="animate-pulse"
              style={{ animationDelay: '0.6s' }}
            />
            <circle
              cx="30"
              cy="80"
              r="8"
              fill="#00897b"
              className="animate-pulse"
              style={{ animationDelay: '0.8s' }}
            />
            
            {/* Center node */}
            <circle cx="100" cy="100" r="12" fill="#004d40" className="animate-pulse" />
            
            {/* Connections */}
            <line x1="100" y1="30" x2="100" y2="100" stroke="#00897b" strokeWidth="2" opacity="0.3" />
            <line x1="170" y1="80" x2="100" y2="100" stroke="#00897b" strokeWidth="2" opacity="0.3" />
            <line x1="150" y1="150" x2="100" y2="100" stroke="#00897b" strokeWidth="2" opacity="0.3" />
            <line x1="50" y1="150" x2="100" y2="100" stroke="#00897b" strokeWidth="2" opacity="0.3" />
            <line x1="30" y1="80" x2="100" y2="100" stroke="#00897b" strokeWidth="2" opacity="0.3" />
          </svg>
        </div>

        {/* Loading Icons */}
        <div className="flex justify-center gap-4 mb-6">
          <Brain className="w-8 h-8 animate-pulse" style={{ color: '#00897b', animationDelay: '0s' }} />
          <Sparkles className="w-8 h-8 animate-pulse" style={{ color: '#00897b', animationDelay: '0.3s' }} />
          <ChartNoAxesColumn className="w-8 h-8 animate-pulse" style={{ color: '#00897b', animationDelay: '0.6s' }} />
          <Rocket className="w-8 h-8 animate-pulse" style={{ color: '#00897b', animationDelay: '0.9s' }} />
        </div>

        {/* Dynamic Message */}
        <p
          className="text-xl font-semibold fade-in"
          key={currentMessage}
          style={{ color: '#004d40' }}
        >
          {messages[currentMessage]}
        </p>

        <p className="text-sm mt-4" style={{ color: '#00695c' }}>
          This usually takes 5-10 seconds...
        </p>
      </div>
    </div>
  );
};

export default LoadingScreen;
