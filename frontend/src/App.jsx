import { BrowserRouter, NavLink, Routes, Route } from "react-router-dom";
import SearchPage from "./pages/SearchPage.jsx";
import HistoryPage from "./pages/HistoryPage.jsx";

function NavTab({ to, children }) {
  return (
    <NavLink
      to={to}
      end
      className={({ isActive }) =>
        `relative pb-3 text-sm font-medium transition-colors duration-200 ${
          isActive ? "text-gold" : "text-paper-faint hover:text-paper-muted"
        }`
      }
    >
      {({ isActive }) => (
        <>
          {children}
          {/* Sliding underline indicator */}
          <span
            className={`absolute bottom-0 left-0 right-0 h-0.5 rounded-full transition-all duration-300 ${
              isActive ? "bg-gold opacity-100" : "opacity-0"
            }`}
          />
        </>
      )}
    </NavLink>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-ink-950">

        {/* Header with subtle bottom border using a gradient so it fades out
            at the edges rather than cutting across the full width */}
        <header className="sticky top-0 z-20 bg-ink-950/90 backdrop-blur-md">
          <div className="mx-auto max-w-2xl px-4 pt-8 pb-0 sm:px-8">
            <div className="animate-fade-up flex items-end justify-between">
              <div>
                <h1 className="font-display text-3xl text-paper leading-none">
                  Songbook
                </h1>
                <p className="mt-1.5 text-sm text-paper-faint">
                  Sing along in any language
                </p>
              </div>
              {/* Decorative note icon — keeps the header from feeling like a
                  generic nav bar, sits in the top-right as a watermark */}
              <span
                className="mb-1 text-4xl select-none opacity-10"
                aria-hidden="true"
              >
                𝄞
              </span>
            </div>

            <nav className="mt-5 flex gap-6 border-b border-ink-800">
              <NavTab to="/">Search</NavTab>
              <NavTab to="/history">History</NavTab>
            </nav>
          </div>
        </header>

        <Routes>
          <Route path="/" element={<SearchPage />} />
          <Route path="/history" element={<HistoryPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
