import { createElement, type ReactNode } from "react";
import HelpImage from "./components/HelpImage";

function inline(value: string): ReactNode[] {
  const result: ReactNode[] = [];
  const pattern = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\[[^\]]+\]\([^\s)]+\)|https?:\/\/[^\s]+)/g;
  let last = 0;
  let match: RegExpExecArray | null;
  while ((match = pattern.exec(value)) !== null) {
    if (match.index > last) result.push(value.slice(last, match.index));
    const token = match[0];
    if (token.startsWith("**")) result.push(createElement("strong", { key: `${match.index}-strong` }, token.slice(2, -2)));
    else if (token.startsWith("*")) result.push(createElement("em", { key: `${match.index}-em` }, token.slice(1, -1)));
    else if (token.startsWith("`")) result.push(createElement("code", { key: `${match.index}-code` }, token.slice(1, -1)));
    else {
      const link = token.match(/^\[([^\]]+)\]\(([^\s)]+)\)$/);
      const href = link?.[2] ?? token;
      const label = link?.[1] ?? token;
      const external = /^https?:\/\//.test(href);
      const safe = href.startsWith("/") || href.startsWith("#") || /^(https?:|mailto:)/i.test(href);
      result.push(safe ? createElement("a", {
        key: `${match.index}-link`, href,
        ...(external ? { target: "_blank", rel: "noopener noreferrer" } : {}),
      }, label) : label);
    }
    last = match.index + token.length;
  }
  if (last < value.length) result.push(value.slice(last));
  return result;
}

export function renderHelpMarkdown(content: string): ReactNode[] {
  const lines = content.replace(/\r\n/g, "\n").split("\n");
  const nodes: ReactNode[] = [];
  let paragraph: string[] = [];
  let list: string[] = [];
  let orderedList: string[] = [];
  let code: string[] = [];
  let inCode = false;

  const flushParagraph = () => { if (paragraph.length) { nodes.push(createElement("p", { key: `p-${nodes.length}` }, inline(paragraph.join(" ")))); paragraph = []; } };
  const flushList = () => { if (list.length) { nodes.push(createElement("ul", { key: `ul-${nodes.length}` }, list.map((item, i) => createElement("li", { key: i }, inline(item))))); list = []; } };
  const flushOrderedList = () => { if (orderedList.length) { nodes.push(createElement("ol", { key: `ol-${nodes.length}` }, orderedList.map((item, i) => createElement("li", { key: i }, inline(item))))); orderedList = []; } };
  const flushCode = () => { if (code.length) { nodes.push(createElement("pre", { key: `pre-${nodes.length}` }, createElement("code", null, code.join("\n")))); code = []; } };

  lines.forEach((line) => {
    if (line.startsWith("```")) { if (inCode) flushCode(); else { flushParagraph(); flushList(); } inCode = !inCode; return; }
    if (inCode) { code.push(line); return; }
    const heading = line.match(/^(#{1,3})\s+(.+)$/);
    if (heading) { flushParagraph(); flushList(); flushOrderedList(); nodes.push(createElement(`h${heading[1].length}`, { key: `h-${nodes.length}` }, inline(heading[2]))); return; }
    if (/^>\s?/.test(line)) { flushParagraph(); flushList(); flushOrderedList(); nodes.push(createElement("blockquote", { key: `q-${nodes.length}` }, inline(line.replace(/^>\s?/, "")))); return; }
    const item = line.match(/^[-*]\s+(.+)$/);
    if (item) { flushParagraph(); flushOrderedList(); list.push(item[1]); return; }
    const orderedItem = line.match(/^\d+[.)]\s+(.+)$/);
    if (orderedItem) { flushParagraph(); flushList(); orderedList.push(orderedItem[1]); return; }
    if (!line.trim()) { flushParagraph(); flushList(); flushOrderedList(); return; }
    const image = line.match(/^!\[([^\]]*)\]\(([^\s)]+)\)$/);
    if (image) { flushParagraph(); flushList(); flushOrderedList(); nodes.push(createElement(HelpImage, { key: `img-${nodes.length}`, src: image[2], alt: image[1] })); return; }
    paragraph.push(line);
  });
  flushParagraph(); flushList(); flushOrderedList(); if (inCode) flushCode();
  return nodes;
}
