import { PLATFORMS, PlatformLogo } from "@/lib/platforms";
import type { PlatformValue } from "@/lib/types";
import { cn } from "@/lib/utils";

export function PlatformIcon({
  platform,
  className = "h-9 w-9",
}: {
  platform: PlatformValue;
  className?: string;
}) {
  return (
    <span className={cn("flex items-center justify-center rounded-lg shadow-sm", PLATFORMS[platform].square, className)}>
      <PlatformLogo platform={platform} className="h-1/2 w-1/2" />
    </span>
  );
}

export function PlatformChip({ platform, name }: { platform: PlatformValue; name?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium",
        PLATFORMS[platform].chip
      )}
    >
      <PlatformLogo platform={platform} className="h-3.5 w-3.5" />
      {PLATFORMS[platform].label}
      {name ? <span className="opacity-70">· {name}</span> : null}
    </span>
  );
}
