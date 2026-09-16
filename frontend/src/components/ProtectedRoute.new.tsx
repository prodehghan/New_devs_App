import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext.new';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { user, isAuthenticated, isLoading } = useAuth();

  console.log(`🛡️ [ProtectedRoute] Rendering. Loading: ${isLoading}, Authenticated: ${isAuthenticated}`);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    console.warn('🛡️ [ProtectedRoute] Not authenticated -> Redirecting to /login');
    return <Navigate to="/login" replace />;
  }

  if (!user?.tenant_id) {
    console.warn('🛡️ [ProtectedRoute] No tenant assigned -> Redirecting to /unauthorized');
    return <Navigate to="/unauthorized" replace />;
  }

  return <>{children}</>;
};
