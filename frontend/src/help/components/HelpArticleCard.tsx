import type { HelpArticle } from "../helpTypes";
type Props = { article: HelpArticle; onOpen: () => void };
export default function HelpArticleCard({ article, onOpen }: Props) { return <article className="help-card"><p className="help-eyebrow">{article.category}</p><h2>{article.title}</h2><p>{article.description}</p><button type="button" onClick={onOpen}>Ver guía <span aria-hidden="true">→</span></button></article>; }
