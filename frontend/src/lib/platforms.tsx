import type { PlatformValue } from "./types";

// Brand glyphs (Simple Icons paths, 24x24 viewBox) rendered in currentColor.
const PATHS: Record<PlatformValue, string> = {
  facebook:
    "M9.101 23.691v-7.98H6.627v-3.667h2.474v-1.58c0-4.085 1.848-5.978 5.858-5.978.401 0 .955.042 1.468.103a8.68 8.68 0 0 1 1.141.195v3.325a8.623 8.623 0 0 0-.653-.036 26.805 26.805 0 0 0-.733-.009c-.707 0-1.259.096-1.675.309a1.686 1.686 0 0 0-.679.622c-.258.42-.374.995-.374 1.752v1.297h3.919l-.386 2.103-.287 1.564h-3.246v8.245C19.396 23.238 24 18.179 24 12.044c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.628 3.874 10.35 9.101 11.647Z",
  linkedin:
    "M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 0 1-2.063-2.065 2.064 2.064 0 1 1 2.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z",
  threads:
    "M12.186 24h-.007c-3.581-.024-6.334-1.205-8.184-3.509C2.35 18.44 1.5 15.586 1.472 12.01v-.017c.03-3.579.879-6.43 2.525-8.482C5.845 1.205 8.6.024 12.18 0h.014c2.746.02 5.043.725 6.826 2.098 1.677 1.29 2.858 3.13 3.509 5.467l-2.04.569c-1.104-3.96-3.898-5.984-8.304-6.015-2.91.022-5.11.936-6.54 2.717C4.307 6.504 3.616 8.914 3.589 12c.027 3.086.718 5.496 2.057 7.164 1.43 1.783 3.631 2.698 6.54 2.717 2.623-.02 4.358-.631 5.8-2.045 1.647-1.613 1.618-3.593 1.09-4.798-.31-.71-.873-1.3-1.634-1.75-.192 1.352-.622 2.446-1.284 3.272-.886 1.102-2.14 1.704-3.73 1.79-1.202.065-2.361-.218-3.259-.801-1.063-.689-1.685-1.74-1.752-2.964-.065-1.19.408-2.285 1.33-3.082.88-.76 2.119-1.207 3.583-1.291a13.853 13.853 0 0 1 3.02.142c-.126-.742-.375-1.332-.74-1.757-.5-.586-1.274-.883-2.299-.89h-.029c-.825 0-1.945.227-2.66 1.298L7.724 7.18c.952-1.428 2.51-2.214 4.43-2.214h.045c3.211.02 5.123 1.99 5.317 5.434.108.046.216.094.32.143 1.49.7 2.58 1.761 3.154 3.07.797 1.82.871 4.79-1.548 7.158-1.85 1.81-4.094 2.628-7.262 2.65Z",
};

// Single source of truth for platform branding: label, brand color, and the
// Tailwind classes used by PlatformBadge. Threads is black/white so its classes
// flip with the theme; Facebook/LinkedIn keep their brand blue in both.
export interface PlatformConfig {
  label: string;
  color: string;
  square: string; // rounded-square avatar classes
  chip: string; // pill chip classes
}

export const PLATFORMS: Record<PlatformValue, PlatformConfig> = {
  facebook: {
    label: "Facebook",
    color: "#1877F2",
    square: "bg-[#1877F2] text-white",
    chip: "bg-[#1877F2]/10 text-[#1877F2] dark:text-[#5b9bf5]",
  },
  linkedin: {
    label: "LinkedIn",
    color: "#0A66C2",
    square: "bg-[#0A66C2] text-white",
    chip: "bg-[#0A66C2]/10 text-[#0A66C2] dark:text-[#5599e0]",
  },
  threads: {
    label: "Threads",
    color: "#000000",
    square: "bg-slate-900 text-white dark:bg-white dark:text-slate-900",
    chip: "bg-slate-900/10 text-slate-900 dark:bg-white/10 dark:text-white",
  },
};

// Max images per post per platform (mirrors PLATFORM_MAX_IMAGES on the backend).
// A post is either 1..N images OR a single video.
export const MAX_IMAGES: Record<PlatformValue, number> = {
  facebook: 10,
  linkedin: 20,
  threads: 20,
};

export function PlatformLogo({
  platform,
  className = "h-4 w-4",
}: {
  platform: PlatformValue;
  className?: string;
}) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className={className} aria-hidden="true">
      <path d={PATHS[platform]} />
    </svg>
  );
}
