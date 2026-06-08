import { toast } from "sonner";
import { ApiError } from "./api";

/** Show a toast for a caught error, using the API-provided message when available. */
export function toastError(err: unknown, fallback: string) {
  toast.error(err instanceof ApiError ? err.message : fallback);
}
