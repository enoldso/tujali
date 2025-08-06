import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import { Container } from 'react-bootstrap';
import { authAPI } from './services/api';
import './App.css';

import NavBar from './components/NavBar';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Patients from './pages/Patients';
import PatientDetail from './pages/PatientDetail';
import Appointments from './pages/Appointments';
import Messages from './pages/Messages';

interface User {
  id: string;
  username: string;
  email: string;
}

const App: React.FC = () => {
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(false);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  
  useEffect(() => {
    const token = localStorage.getItem('token');
    const storedUser = localStorage.getItem('user');
    
    if (token && storedUser) {
      setIsLoggedIn(true);
      setUser(JSON.parse(storedUser));
    }
    
    setLoading(false);
  }, []);
  
  const handleLogin = (token: string, user: User) => {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(user));
    setIsLoggedIn(true);
    setUser(user);
  };
  
  const handleLogout = async () => {
    try {
      await authAPI.logout();
      setIsLoggedIn(false);
      setUser(null);
    } catch (error) {
      console.error('Logout error:', error);
      // Even if API call fails, clear local storage
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      setIsLoggedIn(false);
      setUser(null);
    }
  };
  
  if (loading) {
    return <div>Loading...</div>;
  }
  
  return (
    <Router>
      <div className="App">
        <NavBar isLoggedIn={isLoggedIn} onLogout={handleLogout} />
        <Container className="py-3">
          <Routes>
            <Route 
              path="/login" 
              element={isLoggedIn ? <Navigate to="/dashboard" /> : <Login onLogin={handleLogin} />} 
            />
            <Route 
              path="/dashboard" 
              element={isLoggedIn ? <Dashboard /> : <Navigate to="/login" />} 
            />
            <Route 
              path="/patients" 
              element={isLoggedIn ? <Patients /> : <Navigate to="/login" />} 
            />
            <Route 
              path="/patients/:id" 
              element={isLoggedIn ? <PatientDetail /> : <Navigate to="/login" />} 
            />
            <Route 
              path="/appointments" 
              element={isLoggedIn ? <Appointments /> : <Navigate to="/login" />} 
            />
            <Route 
              path="/messages" 
              element={isLoggedIn ? <Messages /> : <Navigate to="/login" />} 
            />
            <Route 
              path="/" 
              element={<Navigate to={isLoggedIn ? "/dashboard" : "/login"} />} 
            />
          </Routes>
        </Container>
        <footer className="bg-dark text-light py-3 mt-5">
          <Container>
            <div className="text-center">
              <p className="mb-0">Tujali Telehealth &copy; {new Date().getFullYear()} - Bridging healthcare access gaps in Africa</p>
            </div>
          </Container>
        </footer>
      </div>
    </Router>
  );
};

export default App;