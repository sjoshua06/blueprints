import Link from 'next/link';
import { Button } from '@/components/ui/button';

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-background text-foreground">
      {/* Navigation */}
      <nav className="flex items-center justify-between px-6 py-4 border-b border-border">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center text-primary-foreground font-bold text-lg">
            AI
          </div>
          <span className="text-xl font-bold">ChainAI</span>
        </div>
        <div className="flex items-center gap-6">
          <a href="#" className="text-foreground/80 hover:text-foreground transition-colors">Docs</a>
          <a href="#" className="text-foreground/80 hover:text-foreground transition-colors">Pricing</a>
          <a href="#" className="text-foreground/80 hover:text-foreground transition-colors">About</a>
          <Link href="/login" className="text-foreground/80 hover:text-foreground transition-colors">Sign in</Link>
          <Link href="/upload">
            <Button size="sm">Get Started</Button>
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative px-6 py-20 flex flex-col items-center justify-center min-h-[80vh]">
        {/* Background gradient effects */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-1/3 right-0 w-96 h-96 bg-primary/20 rounded-full blur-3xl"></div>
          <div className="absolute bottom-0 left-1/4 w-96 h-96 bg-accent/10 rounded-full blur-3xl"></div>
        </div>

        <div className="relative z-10 max-w-4xl text-center space-y-6">
          <h1 className="text-6xl md:text-7xl font-bold mb-6 leading-tight">
            Unified Supply Chain Intelligence
          </h1>
          
          <p className="text-xl md:text-2xl text-foreground/70">
            AI-powered analysis for identifying component risks, ensuring supplier compatibility, and optimizing your supply chain decisions.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/upload">
              <Button size="lg">
                Start Analysis
              </Button>
            </Link>
            <Button size="lg" variant="outline">
              Watch Demo
            </Button>
          </div>

          {/* Features Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-20">
            <div className="p-6 rounded-lg border border-border bg-card/50">
              <div className="text-3xl mb-3">📊</div>
              <h3 className="text-lg font-semibold mb-2">Risk Analysis</h3>
              <p className="text-foreground/60">Identify internal and external supply chain risks with AI-powered insights</p>
            </div>
            
            <div className="p-6 rounded-lg border border-border bg-card/50">
              <div className="text-3xl mb-3">🔗</div>
              <h3 className="text-lg font-semibold mb-2">Compatibility Check</h3>
              <p className="text-foreground/60">Verify component compatibility across your supply chain network</p>
            </div>
            
            <div className="p-6 rounded-lg border border-border bg-card/50">
              <div className="text-3xl mb-3">⚙️</div>
              <h3 className="text-lg font-semibold mb-2">Supplier Insights</h3>
              <p className="text-foreground/60">Evaluate supplier quality and reliability metrics at a glance</p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-8 px-6 text-center text-foreground/60">
        <p>© 2024 ChainAI. Transforming supply chain intelligence with AI.</p>
      </footer>
    </main>
  );
}
