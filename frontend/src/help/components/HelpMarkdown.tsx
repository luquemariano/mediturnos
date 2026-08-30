import { renderHelpMarkdown } from "../helpMarkdown";

interface HelpMarkdownProps { content: string; }

export default function HelpMarkdown({ content }: HelpMarkdownProps) {
  return <div className="help-markdown">{renderHelpMarkdown(content)}</div>;
}
