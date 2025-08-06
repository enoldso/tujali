import React, { useState, useEffect } from 'react';
import { Navbar, Nav, Container, Button, Badge } from 'react-bootstrap';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { messagesAPI } from '../services/api';

interface NavBarProps {
  isLoggedIn: boolean;
  onLogout: () => void;
}

const NavBar: React.FC<NavBarProps> = ({ isLoggedIn, onLogout }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [unreadCount, setUnreadCount] = useState<number>(0);
  
  // For demo purposes, we'll use a fixed provider ID
  const providerId = '1';
  
  useEffect(() => {
    // If not logged in, don't fetch unread message count
    if (!isLoggedIn) return;
    
    const fetchUnreadCount = async () => {
      try {
        const data = await messagesAPI.getUnreadCount(providerId);
        setUnreadCount(data.count);
      } catch (error) {
        console.error('Error fetching unread message count:', error);
      }
    };
    
    fetchUnreadCount();
    
    // Poll for new messages every 30 seconds
    const interval = setInterval(fetchUnreadCount, 30000);
    
    return () => clearInterval(interval);
  }, [isLoggedIn, providerId]);
  
  const handleLogout = () => {
    onLogout();
    navigate('/login');
  };
  
  return (
    <Navbar bg="dark" variant="dark" expand="lg" className="mb-4">
      <Container>
        <Navbar.Brand as={Link} to="/">
          <img
            src="/logo.png"
            width="30"
            height="30"
            className="d-inline-block align-top me-2"
            alt="Tujali Logo"
          />
          Tujali Telehealth
        </Navbar.Brand>
        
        <Navbar.Toggle aria-controls="basic-navbar-nav" />
        
        <Navbar.Collapse id="basic-navbar-nav">
          {isLoggedIn ? (
            <>
              <Nav className="me-auto">
                <Nav.Link 
                  as={Link} 
                  to="/dashboard"
                  active={location.pathname === '/dashboard'}
                >
                  Dashboard
                </Nav.Link>
                <Nav.Link 
                  as={Link} 
                  to="/patients"
                  active={location.pathname === '/patients'}
                >
                  Patients
                </Nav.Link>
                <Nav.Link 
                  as={Link} 
                  to="/appointments"
                  active={location.pathname === '/appointments'}
                >
                  Appointments
                </Nav.Link>
                <Nav.Link 
                  as={Link} 
                  to="/messages"
                  active={location.pathname === '/messages'}
                >
                  Messages
                  {unreadCount > 0 && (
                    <Badge bg="danger" pill className="ms-1">
                      {unreadCount}
                    </Badge>
                  )}
                </Nav.Link>
              </Nav>
              
              <Nav>
                <Button variant="outline-light" onClick={handleLogout}>
                  Logout
                </Button>
              </Nav>
            </>
          ) : (
            <Nav className="ms-auto">
              <Nav.Link as={Link} to="/login">Login</Nav.Link>
            </Nav>
          )}
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
};

export default NavBar;