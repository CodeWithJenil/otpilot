import LegalLayout from "@/components/LegalLayout";
import Markdown from "@/components/Markdown";
import privacyMarkdown from "../../PRIVACY.md?raw";

const Privacy = () => {
  return (
    <LegalLayout title="Privacy Policy">
      <Markdown markdown={privacyMarkdown} />
    </LegalLayout>
  );
};

export default Privacy;
