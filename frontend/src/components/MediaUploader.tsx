import { useRef, useState, type ChangeEvent } from "react";
import { toast } from "sonner";
import { ImagePlus, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { toastError } from "@/lib/errors";
import type { Media, PlatformValue } from "@/lib/types";
import { MAX_IMAGES } from "@/lib/platforms";
import { Button } from "@/components/ui/button";
import { MediaThumbnail } from "@/components/MediaThumbnail";

export function MediaUploader({
  platform,
  value,
  onChange,
}: {
  platform: PlatformValue;
  value: Media[];
  onChange: (media: Media[]) => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);

  const hasVideo = value.some((m) => m.kind === "video");
  const imageCount = value.filter((m) => m.kind === "image").length;
  const maxImages = MAX_IMAGES[platform];

  function reorder(i: number, dir: -1 | 1) {
    const j = i + dir;
    if (j < 0 || j >= value.length) return;
    const next = value.slice();
    [next[i], next[j]] = [next[j], next[i]];
    onChange(next);
  }

  async function onPick(e: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files ?? []);
    if (inputRef.current) inputRef.current.value = ""; // allow re-selecting same file
    if (!files.length) return;

    setBusy(true);
    const next = [...value];
    try {
      for (const file of files) {
        const isVideo = file.type.startsWith("video/");
        // Enforce: either 1..N images OR a single video — never mixed.
        if (isVideo && (next.length > 0)) {
          toast.error("A video must be the only attachment.");
          break;
        }
        if (!isVideo && next.some((m) => m.kind === "video")) {
          toast.error("Remove the video to attach images.");
          break;
        }
        if (!isVideo && next.filter((m) => m.kind === "image").length >= maxImages) {
          toast.error(`${platform} allows at most ${maxImages} images.`);
          break;
        }
        const media = await api.upload<Media>("/api/media", file);
        next.push(media);
        onChange([...next]);
      }
    } catch (err) {
      toastError(err, "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  const accept = hasVideo
    ? "video/*"
    : imageCount > 0
      ? "image/*"
      : "image/*,video/*";

  return (
    <div className="space-y-2">
      {value.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {value.map((m, i) => (
            <MediaThumbnail
              key={m.id}
              media={m}
              className="h-20 w-20"
              onRemove={() => onChange(value.filter((x) => x.id !== m.id))}
              onMoveLeft={value.length > 1 ? () => reorder(i, -1) : undefined}
              onMoveRight={value.length > 1 ? () => reorder(i, 1) : undefined}
              canMoveLeft={i > 0}
              canMoveRight={i < value.length - 1}
            />
          ))}
        </div>
      )}

      <div className="flex items-center gap-2">
        <input ref={inputRef} type="file" accept={accept} multiple={!hasVideo} className="hidden" onChange={onPick} />
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => inputRef.current?.click()}
          disabled={busy || hasVideo || imageCount >= maxImages}
        >
          {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <ImagePlus className="h-4 w-4" />}
          Add media
        </Button>
        <span className="text-xs text-muted-foreground">
          {hasVideo ? "1 video" : `${imageCount}/${maxImages} images`} · image or video
        </span>
      </div>
    </div>
  );
}
