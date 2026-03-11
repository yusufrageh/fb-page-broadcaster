import { NavLink } from "react-router-dom";

const links = [
  { to: "/", label: "Settings", icon: "S" },
  { to: "/pages", label: "Pages", icon: "P" },
  { to: "/compose", label: "Compose", icon: "C" },
  { to: "/broadcast", label: "Broadcast", icon: "B" },
  { to: "/history", label: "History", icon: "H" },
];

export default function Sidebar() {
  return (
    <aside className="w-64 bg-gray-900 text-white min-h-screen flex flex-col">
      <div className="p-4 border-b border-gray-700">
        <h1 className="text-lg font-bold">FB Broadcaster</h1>
        <p className="text-xs text-gray-400 mt-1">Page Message Broadcaster</p>
      </div>
      <nav className="flex-1 p-4 space-y-1">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                isActive
                  ? "bg-blue-600 text-white"
                  : "text-gray-300 hover:bg-gray-800"
              }`
            }
          >
            <span className="w-6 h-6 rounded bg-gray-700 flex items-center justify-center text-xs font-bold">
              {link.icon}
            </span>
            {link.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
