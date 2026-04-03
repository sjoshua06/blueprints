import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { signUp, signIn } from "../services/auth";
import { createProfile } from "../services/api";

export default function AuthPage() {
  const navigate = useNavigate();
  const [mode, setMode] = useState("signin"); // signin | signup
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  /* form fields */
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [destinationPort, setDestinationPort] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (mode === "signup") {

        // Set flag so the App Router knows to send us to Setup instead of Dashboard
        localStorage.setItem("needsSetup", "true");

        const data = await signUp(email, password);

        /* create profile via backend — user_id extracted from JWT server-side */
        if (data.session) {
          await createProfile({
            user_id: data.user.id,
            full_name: fullName,
            email,
            company_name: companyName || null,
            role: "member",
            destination_port: destinationPort || null,
          });
          navigate("/setup");
        } else {
          /* Supabase requires email confirmation */
          setError(
            "Check your email to confirm your account, then sign in."
          );
          setMode("signin");
        }
      } else {
        await signIn(email, password);
        navigate("/dashboard");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        {/* Decorative element */}
        <div className="auth-card__glow" />

        <div className="auth-card__header">
          <h1 className="auth-card__title">
            {mode === "signin" ? "Welcome Back" : "Get Started"}
          </h1>
          <p className="auth-card__subtitle">
            {mode === "signin"
              ? "Sign in to your supply chain dashboard"
              : "Create your account to begin"}
          </p>
        </div>

        {error && <div className="auth-card__error">{error}</div>}

        <form className="auth-form" onSubmit={handleSubmit}>
          {mode === "signup" && (
            <>
              <div className="form-group">
                <label htmlFor="fullName">Full Name</label>
                <input
                  id="fullName"
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Jane Doe"
                />
              </div>
              <div className="form-group">
                <label htmlFor="companyName">Company Name</label>
                <input
                  id="companyName"
                  type="text"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  placeholder="Acme Corp (optional)"
                />
              </div>
              <div className="form-group">
                <label htmlFor="destinationPort">Destination Port / Place</label>
                <input
                  id="destinationPort"
                  type="text"
                  required
                  value={destinationPort}
                  onChange={(e) => setDestinationPort(e.target.value)}
                  placeholder="e.g. Port of Mumbai, Chennai"
                />
              </div>
            </>
          )}

          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              required
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            className="btn btn--primary btn--full"
            disabled={loading}
          >
            {loading ? (
              <span className="spinner spinner--sm" />
            ) : mode === "signin" ? (
              "Sign In"
            ) : (
              "Create Account"
            )}
          </button>
        </form>

        <div className="auth-card__toggle">
          {mode === "signin" ? (
            <p>
              Don't have an account?{" "}
              <button
                className="link-btn"
                onClick={() => {
                  setMode("signup");
                  setError(null);
                }}
              >
                Sign Up
              </button>
            </p>
          ) : (
            <p>
              Already have an account?{" "}
              <button
                className="link-btn"
                onClick={() => {
                  setMode("signin");
                  setError(null);
                }}
              >
                Sign In
              </button>
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
