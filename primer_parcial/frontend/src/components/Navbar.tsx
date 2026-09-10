import React from 'react';
import { Trophy, Calendar, Shield, Users, Award, AlertTriangle, LogIn, LogOut, Settings } from 'lucide-react';
import { User } from '../types';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  currentUser: User | null;
  onOpenLogin: () => void;
  onLogout: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  currentUser,
  onOpenLogin,
  onLogout
}) => {
  const publicNavItems = [
    { id: 'standings', label: 'Posiciones', icon: Trophy },
    { id: 'fixture', label: 'Fixture', icon: Calendar },
    { id: 'results', label: 'Resultados', icon: Award },
    { id: 'scorers', label: 'Goleadores', icon: Users },
    { id: 'fairplay', label: 'Fair Play', icon: AlertTriangle },
    { id: 'teams', label: 'Equipos', icon: Shield },
  ];

  return (
    <header className="sticky top-0 z-40 glass border-b border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand Logo & Name */}
          <div 
            onClick={() => setActiveTab('standings')} 
            className="flex items-center gap-3 cursor-pointer group"
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-green-400 flex items-center justify-center shadow-lg shadow-emerald-500/20 group-hover:scale-105 transition-transform">
              <Trophy className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="font-heading font-extrabold text-lg sm:text-xl tracking-tight text-white block leading-none">
                LIGA DE BARRIOS <span className="text-emerald-400">& FINCAS</span>
              </span>
              <span className="text-[10px] text-emerald-400 font-semibold uppercase tracking-wider">
                Torneo Amateur Oficial 2026
              </span>
            </div>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-1">
            {publicNavItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {item.label}
                </button>
              );
            })}

            {/* Role-Specific Tabs */}
            {currentUser?.role === 'ADMINISTRADOR' && (
              <button
                onClick={() => setActiveTab('admin')}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeTab === 'admin'
                    ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                    : 'text-purple-400 hover:text-purple-200 hover:bg-purple-950/40'
                }`}
              >
                <Settings className="w-4 h-4" />
                Administración
              </button>
            )}

            {currentUser?.role === 'DELEGADO' && (
              <button
                onClick={() => setActiveTab('delegate')}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeTab === 'delegate'
                    ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                    : 'text-blue-400 hover:text-blue-200 hover:bg-blue-950/40'
                }`}
              >
                <Shield className="w-4 h-4" />
                Mi Equipo
              </button>
            )}
          </nav>

          {/* User Status / Login Button */}
          <div className="flex items-center gap-2">
            {currentUser ? (
              <div className="flex items-center gap-3">
                <div className="text-right hidden sm:block">
                  <div className="text-xs font-semibold text-slate-200 truncate max-w-[150px]">
                    {currentUser.email}
                  </div>
                  <span className={`text-[10px] uppercase font-bold px-1.5 py-0.5 rounded ${
                    currentUser.role === 'ADMINISTRADOR'
                      ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                      : 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                  }`}>
                    {currentUser.role}
                  </span>
                </div>
                <button
                  onClick={onLogout}
                  title="Cerrar Sesión"
                  className="p-2 rounded-lg bg-slate-800 hover:bg-rose-900/40 text-slate-400 hover:text-rose-300 border border-slate-700 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <button
                onClick={onOpenLogin}
                className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium shadow-md shadow-emerald-700/20 transition-all hover:scale-102"
              >
                <LogIn className="w-4 h-4" />
                <span className="hidden sm:inline">Ingresar</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Mobile Horizontal Sub-Navigation */}
      <div className="md:hidden border-t border-slate-800/60 overflow-x-auto scrollbar-none px-2 py-2 flex items-center gap-1.5 bg-slate-950/90">
        {publicNavItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-all ${
                isActive
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                  : 'text-slate-400 hover:bg-slate-900'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              {item.label}
            </button>
          );
        })}

        {currentUser?.role === 'ADMINISTRADOR' && (
          <button
            onClick={() => setActiveTab('admin')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap ${
              activeTab === 'admin'
                ? 'bg-purple-500/30 text-purple-200 border border-purple-500/40'
                : 'text-purple-400 hover:bg-purple-950/40'
            }`}
          >
            <Settings className="w-3.5 h-3.5" />
            Admin
          </button>
        )}

        {currentUser?.role === 'DELEGADO' && (
          <button
            onClick={() => setActiveTab('delegate')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap ${
              activeTab === 'delegate'
                ? 'bg-blue-500/30 text-blue-200 border border-blue-500/40'
                : 'text-blue-400 hover:bg-blue-950/40'
            }`}
          >
            <Shield className="w-3.5 h-3.5" />
            Mi Equipo
          </button>
        )}
      </div>
    </header>
  );
};
