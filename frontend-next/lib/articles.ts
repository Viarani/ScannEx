export type Article = {
  slug: string;
  title: string;
  excerpt: string;
  sections: { heading: string; body: string }[];
};

export const articles: Article[] = [
  {
    slug: "understanding-e-waste",
    title: "Understanding E-Waste",
    excerpt: "What e-waste is, what valuable materials live inside, and why it deserves a second look.",
    sections: [
      { heading: "What is e-waste?", body: "E-waste is any discarded electrical or electronic device — from phones and laptops to chargers, batteries, and appliances. As we upgrade faster, the volume grows. Globally, over 50 million tonnes are generated each year." },
      { heading: "What valuable materials are inside?", body: "Even small devices contain copper, aluminum, glass, and trace amounts of gold, silver, and rare earth elements. A tonne of circuit boards can hold more gold than a tonne of ore. Recovery is possible when items are collected properly." },
      { heading: "Why improper disposal can be harmful", body: "Batteries, screens, and boards can leach metals or release fumes if broken, burned, or landfilled. Keeping them dry, intact, and separate helps protect people and the environment." },
      { heading: "What can we do?", body: "Recognize what you have, keep it together, and choose a responsible next step — reuse, repair, or channel it to a certified recycler. Start by identifying your item." },
    ],
  },
  {
    slug: "why-recycling-matters",
    title: "Why Recycling Matters",
    excerpt: "Recycling keeps materials in use and reduces the need for new extraction.",
    sections: [
      { heading: "Keeping materials circular", body: "Recycling recovers metals and plastics so they re-enter manufacturing, reducing mining and energy use." },
      { heading: "Community impact", body: "Local collection creates jobs, supports repair culture, and funds community programs when handled through ethical channels." },
      { heading: "Your contribution", body: "Even one phone handed in correctly keeps hazardous parts out of landfill and valuable parts in the loop." },
    ],
  },
  {
    slug: "your-role-and-community",
    title: "Your Role & Community",
    excerpt: "How individuals and communities power circularity together.",
    sections: [
      { heading: "At home", body: "Store unused electronics in a dry place, keep batteries separate, and avoid breaking screens or boards." },
      { heading: "In your neighborhood", body: "Community drives, repair cafés, and school programs help neighbours learn and act together." },
      { heading: "Together", body: "When many households participate, collection becomes viable and recovery scales." },
    ],
  },
  {
    slug: "where-to-recycle-safely",
    title: "Where to Recycle Safely",
    excerpt: "Find a safe, certified path for your item.",
    sections: [
      { heading: "Certified collectors", body: "Look for recyclers or take-back programs that provide documentation and safe handling for batteries and boards." },
      { heading: "Retail and manufacturer programs", body: "Many brands and retailers offer drop-off for phones, laptops, and accessories." },
      { heading: "What to ask", body: "Ask where materials go next and whether batteries are handled separately." },
    ],
  },
  {
    slug: "when-to-let-go",
    title: "When to Let Go of Devices",
    excerpt: "Signs it’s time to repair, pass on, or recycle.",
    sections: [
      { heading: "Repair first", body: "If a device still functions with a battery or screen fix, repair extends its life the most." },
      { heading: "Pass it on", body: "Working devices can be donated or resold — ensure data is wiped." },
      { heading: "Recycle when done", body: "If it’s broken, obsolete, or unsafe, route it to recycling rather than storage." },
    ],
  },
  {
    slug: "how-to-recycle-step-by-step",
    title: "How to Recycle Step by Step",
    excerpt: "A simple, safe routine for any electronic item.",
    sections: [
      { heading: "01 Prepare", body: "Back up and wipe personal data. Keep the item intact and dry." },
      { heading: "02 Sort", body: "Separate batteries, cables, and devices. Keep screens unbroken." },
      { heading: "03 Drop or schedule", body: "Use a certified drop-off or schedule a pickup if available in your area." },
      { heading: "04 Track", body: "Keep the receipt or tracking number for your records." },
    ],
  },
];

export function getArticle(slug: string) { return articles.find((a) => a.slug === slug); }
