import Hero from "@/components/Hero";
import HowItWorks from "@/components/HowItWorks";
import FeaturesGrid from "@/components/FeaturesGrid";
import InstallStrip from "@/components/InstallStrip";
import Footer from "@/components/Footer";
import AboutDeveloper from "@/components/AboutDeveloper";
import CustomCursor from "@/components/CustomCursor";
import GrainOverlay from "@/components/GrainOverlay";

const Index = () => {
  return (
    <main className="min-h-screen bg-background text-foreground">
      <CustomCursor />
      <GrainOverlay />
      <Hero />
      <HowItWorks />
      <FeaturesGrid />
      <InstallStrip />
      <AboutDeveloper />
      <Footer />
    </main>
  );
};

export default Index;
