import type { PlatformValue } from "@/types/api";

interface PlatformConfig {
  value: PlatformValue;
  label: string;
  color: string;
  MAX_IMAGES: number;
}

export const PLATFORMS: Record<PlatformValue, PlatformConfig> = {
  facebook: { value: "facebook", label: "Facebook", color: "#1877f2", MAX_IMAGES: 10 },
  linkedin: { value: "linkedin", label: "LinkedIn", color: "#0a66c2", MAX_IMAGES: 9 },
  threads: { value: "threads", label: "Threads", color: "#000000", MAX_IMAGES: 10 },
};

export const PLATFORM_LIST = Object.values(PLATFORMS);
