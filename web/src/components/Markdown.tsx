import React from "react";
import { Link } from "react-router-dom";

type MarkdownProps = {
  markdown: string;
};

const isExternalHref = (href: string) => /^https?:\/\//i.test(href) || /^mailto:/i.test(href);

const renderInline = (text: string) => {
  const nodes: React.ReactNode[] = [];
  let remaining = text;
  let key = 0;

  const pushText = (value: string) => {
    if (!value) return;
    nodes.push(value);
  };

  while (remaining.length > 0) {
    const linkMatch = remaining.match(/\[([^\]]+)\]\(([^)]+)\)/);
    const boldMatch = remaining.match(/\*\*([^*]+)\*\*/);
    const codeMatch = remaining.match(/`([^`]+)`/);

    const matches = [linkMatch, boldMatch, codeMatch]
      .filter((m): m is RegExpMatchArray => Boolean(m && typeof m.index === "number"))
      .sort((a, b) => (a.index ?? 0) - (b.index ?? 0));

    if (matches.length === 0) {
      pushText(remaining);
      break;
    }

    const match = matches[0];
    const index = match.index ?? 0;
    pushText(remaining.slice(0, index));

    if (match === linkMatch) {
      const label = match[1];
      const href = match[2];
      if (href.startsWith("/") && !isExternalHref(href)) {
        nodes.push(
          <Link key={`l-${key++}`} to={href} className="underline underline-offset-4 hover:text-primary">
            {label}
          </Link>,
        );
      } else {
        nodes.push(
          <a
            key={`a-${key++}`}
            href={href}
            target={isExternalHref(href) ? "_blank" : undefined}
            rel={isExternalHref(href) ? "noopener noreferrer" : undefined}
            className="underline underline-offset-4 hover:text-primary"
          >
            {label}
          </a>,
        );
      }
      remaining = remaining.slice(index + match[0].length);
      continue;
    }

    if (match === boldMatch) {
      nodes.push(
        <strong key={`b-${key++}`} className="font-semibold text-foreground">
          {match[1]}
        </strong>,
      );
      remaining = remaining.slice(index + match[0].length);
      continue;
    }

    // inline code
    nodes.push(
      <code key={`c-${key++}`} className="rounded bg-muted px-1 py-0.5 font-mono text-[0.95em]">
        {match[1]}
      </code>,
    );
    remaining = remaining.slice(index + match[0].length);
  }

  return nodes;
};

const splitTableRow = (line: string) =>
  line
    .trim()
    .replace(/^\|/, "")
    .replace(/\|$/, "")
    .split("|")
    .map((c) => c.trim());

const isTableSeparatorRow = (line: string) => {
  const cells = splitTableRow(line);
  return (
    cells.length > 0 &&
    cells.every((cell) => cell.length > 0 && /^[\s:-]+$/.test(cell) && cell.replace(/[\s:-]/g, "").length === 0)
  );
};

const Markdown = ({ markdown }: MarkdownProps) => {
  const lines = markdown.replace(/\r\n/g, "\n").split("\n");
  const blocks: React.ReactNode[] = [];
  let i = 0;
  let key = 0;

  const pushParagraph = (paragraphLines: string[]) => {
    if (paragraphLines.length === 0) return;
    const parts: React.ReactNode[] = [];
    for (let idx = 0; idx < paragraphLines.length; idx++) {
      const line = paragraphLines[idx];
      const hasHardBreak = line.endsWith("  ");
      parts.push(<React.Fragment key={`p-${key++}`}>{renderInline(hasHardBreak ? line.slice(0, -2) : line)}</React.Fragment>);
      if (hasHardBreak || idx < paragraphLines.length - 1) parts.push(<br key={`br-${key++}`} />);
    }
    blocks.push(
      <p key={`para-${key++}`} className="text-sm leading-6 text-muted-foreground">
        {parts}
      </p>,
    );
  };

  while (i < lines.length) {
    const line = lines[i];

    if (!line.trim()) {
      i++;
      continue;
    }

    // fenced code block
    if (line.trim().startsWith("```")) {
      const fence = line.trim();
      const code: string[] = [];
      i++;
      while (i < lines.length && lines[i].trim() !== fence) {
        code.push(lines[i]);
        i++;
      }
      i++; // consume closing fence
      blocks.push(
        <pre key={`pre-${key++}`} className="overflow-x-auto rounded-lg border border-border bg-muted p-4 text-sm">
          <code className="font-mono">{code.join("\n")}</code>
        </pre>,
      );
      continue;
    }

    // horizontal rule
    if (/^---\s*$/.test(line.trim())) {
      blocks.push(<hr key={`hr-${key++}`} className="my-6 border-border" />);
      i++;
      continue;
    }

    // headings
    const headingMatch = line.match(/^(#{1,6})\s+(.+)$/);
    if (headingMatch) {
      const level = headingMatch[1].length;
      const text = headingMatch[2].trim();
      const Tag = (`h${Math.min(level, 3)}` as unknown) as "h1" | "h2" | "h3";
      const className =
        Tag === "h1"
          ? "text-3xl font-bold tracking-tight"
          : Tag === "h2"
            ? "mt-8 text-xl font-semibold tracking-tight"
            : "mt-6 text-lg font-semibold tracking-tight";
      blocks.push(
        <Tag key={`h-${key++}`} className={className}>
          {renderInline(text)}
        </Tag>,
      );
      i++;
      continue;
    }

    // table (GitHub-flavored pipe table)
    if (line.includes("|") && i + 1 < lines.length && isTableSeparatorRow(lines[i + 1])) {
      const header = splitTableRow(line);
      i += 2; // consume header + separator
      const rows: string[][] = [];
      while (i < lines.length && lines[i].trim() && lines[i].includes("|")) {
        rows.push(splitTableRow(lines[i]));
        i++;
      }

      blocks.push(
        <div key={`tblwrap-${key++}`} className="overflow-x-auto">
          <table className="w-full border-collapse text-left text-sm">
            <thead>
              <tr className="border-b border-border">
                {header.map((cell) => (
                  <th key={`th-${key++}`} className="px-3 py-2 font-semibold text-foreground">
                    {renderInline(cell)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={`tr-${key++}`} className="border-b border-border/60 last:border-0">
                  {row.map((cell) => (
                    <td key={`td-${key++}`} className="px-3 py-2 text-muted-foreground align-top">
                      {renderInline(cell)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>,
      );
      continue;
    }

    // unordered list
    if (/^\s*-\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\s*-\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*-\s+/, ""));
        i++;
      }
      blocks.push(
        <ul key={`ul-${key++}`} className="list-disc pl-6 text-sm leading-6 text-muted-foreground">
          {items.map((item) => (
            <li key={`li-${key++}`}>{renderInline(item)}</li>
          ))}
        </ul>,
      );
      continue;
    }

    // ordered list
    if (/^\s*\d+\.\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\s*\d+\.\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*\d+\.\s+/, ""));
        i++;
      }
      blocks.push(
        <ol key={`ol-${key++}`} className="list-decimal pl-6 text-sm leading-6 text-muted-foreground">
          {items.map((item) => (
            <li key={`oli-${key++}`}>{renderInline(item)}</li>
          ))}
        </ol>,
      );
      continue;
    }

    // paragraph (collect until blank line)
    const paragraphLines: string[] = [];
    while (i < lines.length && lines[i].trim()) {
      paragraphLines.push(lines[i]);
      i++;
    }
    pushParagraph(paragraphLines);
  }

  return <div className="space-y-4">{blocks}</div>;
};

export default Markdown;

