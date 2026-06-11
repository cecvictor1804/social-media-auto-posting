import { Route, Routes } from "react-router-dom";
import { RequireAuth } from "@/components/RequireAuth";
import { AppShell } from "@/components/AppShell";
import Login from "@/pages/Login";
import Compose from "@/pages/Compose";
import Queue from "@/pages/Queue";
import CalendarPage from "@/pages/Calendar";
import Accounts from "@/pages/Accounts";
import Review from "@/pages/Review";
import UsersPage from "@/pages/Users";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        element={
          <RequireAuth>
            <AppShell />
          </RequireAuth>
        }
      >
        <Route path="/" element={<Compose />} />
        <Route path="/queue" element={<Queue />} />
        <Route path="/calendar" element={<CalendarPage />} />
        <Route path="/accounts" element={<Accounts />} />
        <Route path="/posts/:id" element={<Review />} />
        <Route path="/users" element={<UsersPage />} />
      </Route>
    </Routes>
  );
}
