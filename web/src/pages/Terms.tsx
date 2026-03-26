import LegalLayout from "@/components/LegalLayout";
import Markdown from "@/components/Markdown";
import termsMarkdown from "../../TERMS.md?raw";

const Terms = () => {
  return (
    <LegalLayout title="Terms of Service">
      <Markdown markdown={termsMarkdown} />
    </LegalLayout>
  );
};

export default Terms;
