import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

describe("sitemap público", () => {
  it("contiene la landing de software para consultorios y conserva XML válido", () => {
    const xml = readFileSync(resolve(__dirname, "../public/sitemap.xml"), "utf8");
    const parsed = new DOMParser().parseFromString(xml, "application/xml");
    const url = "https://turnelia.com.ar/software-para-consultorios";
    const locations = Array.from(parsed.getElementsByTagNameNS("*", "loc"), (element) => element.textContent);

    expect(parsed.querySelector("parsererror")).toBeNull();
    expect(locations.filter((location) => location === url)).toHaveLength(1);
  });

  it("contiene la landing de sistema de turnos", () => {
    const xml = readFileSync(resolve(__dirname, "../public/sitemap.xml"), "utf8");
    const parsed = new DOMParser().parseFromString(xml, "application/xml");
    const url = "https://turnelia.com.ar/sistema-de-turnos";
    const locations = Array.from(parsed.getElementsByTagNameNS("*", "loc"), (element) => element.textContent);

    expect(parsed.querySelector("parsererror")).toBeNull();
    expect(locations.filter((location) => location === url)).toHaveLength(1);
  });

  it("contiene una sola URL para la landing de psicopedagogos", () => {
    const xml = readFileSync(resolve(__dirname, "../public/sitemap.xml"), "utf8");
    const parsed = new DOMParser().parseFromString(xml, "application/xml");
    const url = "https://turnelia.com.ar/para-psicopedagogos";
    const locations = Array.from(parsed.getElementsByTagNameNS("*", "loc"), (element) => element.textContent);

    expect(parsed.querySelector("parsererror")).toBeNull();
    expect(locations.filter((location) => location === url)).toHaveLength(1);
  });
});
