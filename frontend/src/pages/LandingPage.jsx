import { Link } from "react-router-dom";
import { ArrowRight, ShieldCheck, Globe, Activity, Anchor } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="landing-page">
      <nav className="landing-nav">
        <div className="landing-logo">
          <Anchor className="landing-logo-icon" />
          <span>Blueprints Risk</span>
        </div>
        <div className="landing-nav-links">
          <Link to="/auth" className="btn btn--secondary">Sign In</Link>
          <Link to="/auth" className="btn btn--primary">Get Started</Link>
        </div>
      </nav>

      <main className="landing-main">
        <div className="hero-orb hero-orb-1"></div>
        <div className="hero-orb hero-orb-2"></div>
        
        <header className="hero">
          <h1 className="hero-title">
            Supply Chain Intelligence,<br />
            <span className="hero-title-highlight">Powered by AI</span>
          </h1>
          <p className="hero-subtitle">
            Anticipate risks, optimize inventory, and gain real-time visibility into your global suppliers before disruptions happen.
          </p>
          <div className="hero-actions">
            <Link to="/auth" className="btn btn--primary btn--lg">
              Start Free Trial
              <ArrowRight size={20} />
            </Link>
            <Link to="/auth" className="btn btn--secondary btn--lg">
              View Demo
            </Link>
          </div>
        </header>

        <section className="features-grid">
          <div className="feature-card">
            <div className="feature-icon-wrapper">
              <ShieldCheck size={28} />
            </div>
            <h3>Supplier Risk Analysis</h3>
            <p>Continuously monitor financial stability and overall reliability for thousands of vendors globally.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon-wrapper">
              <Activity size={28} />
            </div>
            <h3>BOM Intelligence</h3>
            <p>Automatically analyze your Bill of Materials to find single points of failure and alternative sourcing.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon-wrapper">
              <Globe size={28} />
            </div>
            <h3>Live Shipping Data</h3>
            <p>Integrate with actual port capacities, congestion data, and maritime routing down to the vessel level.</p>
          </div>
        </section>
      </main>
    </div>
  );
}
