import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Table, Badge } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import { dashboardAPI, patientsAPI, appointmentsAPI, messagesAPI } from '../services/api';

interface DashboardStats {
  totalPatients: number;
  pendingAppointments: number;
  unreadMessages: number;
}

interface RecentPatient {
  id: string;
  name: string;
  phone_number: string;
  created_at: string;
}

interface RecentAppointment {
  id: string;
  patient_id: string;
  patient_name: string;
  date: string;
  time: string;
  status: string;
}

interface RecentMessage {
  id: string;
  patient_id: string;
  patient_name: string;
  content: string;
  created_at: string;
}

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats>({
    totalPatients: 0,
    pendingAppointments: 0,
    unreadMessages: 0
  });
  const [recentPatients, setRecentPatients] = useState<RecentPatient[]>([]);
  const [recentAppointments, setRecentAppointments] = useState<RecentAppointment[]>([]);
  const [recentMessages, setRecentMessages] = useState<RecentMessage[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  
  // For demo purposes, we'll use a fixed provider ID
  const providerId = '1';
  
  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        
        // Fetch all data in parallel
        const [statsData, patientsData, appointmentsData, messagesData] = await Promise.all([
          dashboardAPI.getStats(providerId),
          dashboardAPI.getRecentPatients(),
          dashboardAPI.getRecentAppointments(providerId),
          dashboardAPI.getRecentMessages(providerId)
        ]);
        
        setStats(statsData);
        setRecentPatients(patientsData);
        setRecentAppointments(appointmentsData);
        setRecentMessages(messagesData);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchDashboardData();
  }, [providerId]);
  
  // Format date to display in a readable format
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };
  
  // Get appropriate badge color for appointment status
  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case 'confirmed':
        return 'success';
      case 'pending':
        return 'warning';
      case 'cancelled':
        return 'danger';
      case 'completed':
        return 'info';
      default:
        return 'secondary';
    }
  };
  
  // Render loading state
  if (loading) {
    return (
      <Container className="py-4">
        <div className="text-center">
          <p>Loading dashboard...</p>
        </div>
      </Container>
    );
  }
  
  return (
    <Container className="py-4">
      <h1 className="mb-4">Dashboard</h1>
      
      {/* Stats Cards */}
      <Row className="mb-4">
        <Col md={4}>
          <Card className="text-center h-100 shadow-sm">
            <Card.Body>
              <Card.Title>Patients</Card.Title>
              <h2 className="display-4">{stats.totalPatients}</h2>
              <Card.Text>Total registered patients</Card.Text>
              <Link to="/patients" className="btn btn-sm btn-outline-primary">View All</Link>
            </Card.Body>
          </Card>
        </Col>
        
        <Col md={4}>
          <Card className="text-center h-100 shadow-sm">
            <Card.Body>
              <Card.Title>Appointments</Card.Title>
              <h2 className="display-4">{stats.pendingAppointments}</h2>
              <Card.Text>Pending appointments</Card.Text>
              <Link to="/appointments" className="btn btn-sm btn-outline-primary">View All</Link>
            </Card.Body>
          </Card>
        </Col>
        
        <Col md={4}>
          <Card className="text-center h-100 shadow-sm">
            <Card.Body>
              <Card.Title>Messages</Card.Title>
              <h2 className="display-4">{stats.unreadMessages}</h2>
              <Card.Text>Unread messages</Card.Text>
              <Link to="/messages" className="btn btn-sm btn-outline-primary">View All</Link>
            </Card.Body>
          </Card>
        </Col>
      </Row>
      
      {/* Recent Patients */}
      <Card className="mb-4 shadow-sm">
        <Card.Header className="bg-light">
          <div className="d-flex justify-content-between align-items-center">
            <h5 className="mb-0">Recent Patients</h5>
            <Link to="/patients" className="btn btn-sm btn-outline-primary">View All</Link>
          </div>
        </Card.Header>
        <Card.Body>
          {recentPatients.length === 0 ? (
            <p className="text-center text-muted my-3">No recent patients</p>
          ) : (
            <Table hover responsive>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Phone Number</th>
                  <th>Registration Date</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {recentPatients.map(patient => (
                  <tr key={patient.id}>
                    <td>{patient.name}</td>
                    <td>{patient.phone_number}</td>
                    <td>{formatDate(patient.created_at)}</td>
                    <td>
                      <Link to={`/patients/${patient.id}`} className="btn btn-sm btn-outline-info">
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </Card.Body>
      </Card>
      
      {/* Recent Appointments */}
      <Card className="mb-4 shadow-sm">
        <Card.Header className="bg-light">
          <div className="d-flex justify-content-between align-items-center">
            <h5 className="mb-0">Recent Appointments</h5>
            <Link to="/appointments" className="btn btn-sm btn-outline-primary">View All</Link>
          </div>
        </Card.Header>
        <Card.Body>
          {recentAppointments.length === 0 ? (
            <p className="text-center text-muted my-3">No recent appointments</p>
          ) : (
            <Table hover responsive>
              <thead>
                <tr>
                  <th>Patient</th>
                  <th>Date</th>
                  <th>Time</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {recentAppointments.map(appointment => (
                  <tr key={appointment.id}>
                    <td>
                      <Link to={`/patients/${appointment.patient_id}`}>
                        {appointment.patient_name}
                      </Link>
                    </td>
                    <td>{appointment.date}</td>
                    <td>{appointment.time}</td>
                    <td>
                      <Badge bg={getStatusBadge(appointment.status)}>
                        {appointment.status.charAt(0).toUpperCase() + appointment.status.slice(1)}
                      </Badge>
                    </td>
                    <td>
                      <Link to={`/appointments`} className="btn btn-sm btn-outline-info">
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </Card.Body>
      </Card>
      
      {/* Recent Messages */}
      <Card className="shadow-sm">
        <Card.Header className="bg-light">
          <div className="d-flex justify-content-between align-items-center">
            <h5 className="mb-0">Recent Messages</h5>
            <Link to="/messages" className="btn btn-sm btn-outline-primary">View All</Link>
          </div>
        </Card.Header>
        <Card.Body>
          {recentMessages.length === 0 ? (
            <p className="text-center text-muted my-3">No recent messages</p>
          ) : (
            <Table hover responsive>
              <thead>
                <tr>
                  <th>Patient</th>
                  <th>Message</th>
                  <th>Date</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {recentMessages.map(message => (
                  <tr key={message.id}>
                    <td>
                      <Link to={`/patients/${message.patient_id}`}>
                        {message.patient_name}
                      </Link>
                    </td>
                    <td className="text-truncate" style={{ maxWidth: '300px' }}>
                      {message.content}
                    </td>
                    <td>{formatDate(message.created_at)}</td>
                    <td>
                      <Link to={`/messages`} className="btn btn-sm btn-outline-info">
                        Reply
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </Card.Body>
      </Card>
    </Container>
  );
};

export default Dashboard;