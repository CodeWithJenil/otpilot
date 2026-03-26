import LogoMark from "@/components/LogoMark";
import { Link } from "react-router-dom";

const Footer = () => (
  <footer className="border-t border-border py-8">
    <div className="container mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
      <LogoMark compact />
      <span className="text-sm text-muted-foreground font-body">Built with Python</span>
      <div className="flex items-center gap-4 flex-wrap justify-center">
        <Link
          to="/privacy"
          className="text-sm text-muted-foreground hover:text-primary font-mono transition-colors duration-200"
        >
          Privacy
        </Link>
        <Link
          to="/terms"
          className="text-sm text-muted-foreground hover:text-primary font-mono transition-colors duration-200"
        >
          Terms
        </Link>
        <a
          href="https://github.com/codewithjenil/otpilot"
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm text-muted-foreground hover:text-primary font-mono transition-colors duration-200"
        >
          GitHub
        </a>
        <a
          href="https://jenilbuildspace.vercel.app"
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm text-muted-foreground hover:text-primary font-mono transition-colors duration-200"
        >
          About Developer
        </a>
      </div>
    </div>
  </footer>
);

export default Footer;
