import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { CalendarDays } from "lucide-react";
import { api } from "@/lib/api";
import { qk } from "@/lib/queryKeys";
import type { CalendarDay } from "@/lib/types";
import { PageHeader } from "@/components/PageHeader";
import { PlatformChip } from "@/components/PlatformBadge";
import { StatusPill } from "@/components/StatusPill";
import { EmptyState } from "@/components/EmptyState";
import { LoadingSkeletons } from "@/components/Skeletons";
import { Card, CardContent } from "@/components/ui/card";

export default function CalendarPage() {
  const { data, isLoading } = useQuery({
    queryKey: qk.calendar,
    queryFn: () => api.get<CalendarDay[]>("/api/calendar"),
  });
  const days = data ?? [];

  return (
    <>
      <PageHeader title="Calendar" subtitle="Scheduled and published posts, grouped by day." />

      {isLoading && <LoadingSkeletons count={2} className="h-24 w-full" />}

      {!isLoading && days.length === 0 && (
        <EmptyState Icon={CalendarDays}>Nothing scheduled yet.</EmptyState>
      )}

      <div className="space-y-6">
        {days.map((day) => (
          <div key={day.day} className="fade-in">
            <div className="mb-2 flex items-center gap-2">
              <CalendarDays className="h-4 w-4 text-primary" />
              <h2 className="text-sm font-semibold">{day.day}</h2>
              <span className="text-xs text-muted-foreground">· {day.posts.length} post{day.posts.length === 1 ? "" : "s"}</span>
            </div>
            <Card>
              <CardContent className="divide-y p-0">
                {day.posts.map((post) => (
                  <Link
                    key={post.id}
                    to={`/posts/${post.id}`}
                    className="flex items-center gap-3 px-4 py-3 transition-colors hover:bg-accent"
                  >
                    <span className="w-14 shrink-0 text-sm font-medium tabular-nums text-muted-foreground">
                      {post.scheduled_time_display.split(" ")[1] ?? ""}
                    </span>
                    <div className="flex flex-wrap items-center gap-1.5">
                      {post.targets.map((t) => (
                        <PlatformChip key={t.id} platform={t.platform} />
                      ))}
                    </div>
                    <span className="flex-1 truncate text-sm text-foreground/80">{post.body}</span>
                    <StatusPill status={post.status} />
                  </Link>
                ))}
              </CardContent>
            </Card>
          </div>
        ))}
      </div>
    </>
  );
}
