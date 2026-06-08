import { Skeleton } from "@/components/ui/skeleton";

export function LoadingSkeletons({ count = 3, className = "h-28 w-full" }: { count?: number; className?: string }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <Skeleton key={i} className={className} />
      ))}
    </div>
  );
}
