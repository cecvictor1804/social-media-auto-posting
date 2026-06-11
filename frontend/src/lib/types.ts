// Wire types mirroring app/schemas.py.

export type PlatformValue = "facebook" | "linkedin" | "threads";

export type PostStatus =
  | "draft"
  | "pending_review"
  | "approved"
  | "scheduled"
  | "publishing"
  | "published"
  | "failed";

export type TargetStatus = "pending" | "publishing" | "published" | "failed";

// Manual "add account" form (mirrors ManualAccountIn on the backend). Differs
// from `Account` because it carries the raw secrets that are never read back.
export interface ManualAccountForm {
  display_name: string;
  platform_account_id: string;
  access_token: string;
  refresh_token: string;
  token_expires_at: string;
}

export interface User {
  id: number;
  email: string;
  is_admin: boolean;
}

export interface AdminUser {
  id: number;
  email: string;
  is_admin: boolean;
  is_active: boolean;
  created_at: string | null;
}

export interface ModelInfo {
  id: string;
  label: string;
  provider: string;
}

export interface PlatformMeta {
  value: PlatformValue;
  label: string;
  color: string;
  char_limit: number;
}

export interface Meta {
  models: ModelInfo[];
  default_model: string;
  tones: string[];
  platforms: PlatformMeta[];
}

export interface Account {
  id: number;
  platform: PlatformValue;
  display_name: string;
  platform_account_id: string;
  token_set: boolean;
  token_expires_at: string | null;
  token_expires_display: string | null;
  is_active: boolean;
}

export interface AccountsResponse {
  accounts: Account[];
  configured: Record<PlatformValue, boolean>;
}

export interface Media {
  id: number;
  url: string;
  content_type: string;
  kind: "image" | "video";
  filename: string;
}

export interface DraftItem {
  account_id: number;
  platform: PlatformValue;
  display_name: string;
  body: string;
  limit: number;
  media: Media[];
}

export interface Target {
  id: number;
  platform: PlatformValue;
  display_name: string;
  status: TargetStatus;
  platform_post_id: string | null;
  error_message: string | null;
}

export interface Post {
  id: number;
  body: string;
  status: PostStatus;
  source: string;
  ai_provider: string | null;
  ai_model: string | null;
  scheduled_time: string | null;
  scheduled_time_display: string;
  created_at: string | null;
  targets: Target[];
  media: Media[];
}

export interface CalendarDay {
  day: string;
  posts: Post[];
}
