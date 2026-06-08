import { ArrowLeft, ArrowRight, Film, X } from "lucide-react";
import type { Media } from "@/lib/types";
import { cn } from "@/lib/utils";

interface Props {
  media: Media;
  className?: string;
  /** Wrap video tiles in a link to open the file (used in read-only views). */
  videoLink?: boolean;
  onRemove?: () => void;
  onMoveLeft?: () => void;
  onMoveRight?: () => void;
  canMoveLeft?: boolean;
  canMoveRight?: boolean;
}

export function MediaThumbnail({
  media,
  className = "h-24 w-24",
  videoLink = false,
  onRemove,
  onMoveLeft,
  onMoveRight,
  canMoveLeft,
  canMoveRight,
}: Props) {
  const showControls = !!onMoveLeft || !!onMoveRight;
  const inner =
    media.kind === "image" ? (
      <img src={media.url} alt={media.filename} className="h-full w-full object-cover" />
    ) : videoLink ? (
      <a
        href={media.url}
        target="_blank"
        rel="noreferrer"
        className="flex h-full w-full items-center justify-center text-muted-foreground"
      >
        <Film className="h-7 w-7" />
      </a>
    ) : (
      <div className="flex h-full w-full items-center justify-center text-muted-foreground">
        <Film className="h-6 w-6" />
      </div>
    );

  return (
    <div className={cn("group relative overflow-hidden rounded-lg border bg-muted", className)}>
      {inner}
      {onRemove && (
        <button
          type="button"
          onClick={onRemove}
          className="absolute right-0.5 top-0.5 rounded-full bg-black/60 p-0.5 text-white opacity-0 transition group-hover:opacity-100"
          aria-label="Remove"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      )}
      {showControls && (
        <div className="absolute bottom-0 left-0 right-0 flex justify-between bg-black/50 px-0.5 opacity-0 transition group-hover:opacity-100">
          <button type="button" onClick={onMoveLeft} className="text-white disabled:opacity-30" disabled={!canMoveLeft} aria-label="Move left">
            <ArrowLeft className="h-3.5 w-3.5" />
          </button>
          <button type="button" onClick={onMoveRight} className="text-white disabled:opacity-30" disabled={!canMoveRight} aria-label="Move right">
            <ArrowRight className="h-3.5 w-3.5" />
          </button>
        </div>
      )}
    </div>
  );
}
