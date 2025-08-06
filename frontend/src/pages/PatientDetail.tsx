import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Container, Row, Col, Card, ListGroup, Badge, Tab, Nav } from 'react-bootstrap';
import { patientsAPI, appointmentsAPI, messagesAPI } from '../services/api';

interface Patient {
  id: string;
  name: string;
  phone_number: string;
  age: number;
  gender: string;
  location: string;
  language: string;
  created_at: string;
  symptoms?: string[];
}

interface Appointment {
  id: string;
  date: string;
  time: string;
  status: string;
  notes: string;
  created_at: string;
}

interface Message {
  id: string;
  content: string;
  sender_type: string;
  is_read: boolean;
  created_at: string;
}

const PatientDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [patient, setPatient] = useState<Patient | null>(null);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    const fetchPatientData = async () => {
      if (!id) return;
      
      try {
        setLoading(true);
        
        // Fetch patient details, appointments, and messages in parallel
        const [patientRes, appointmentsRes, messagesRes] = await Promise.all([
          patientsAPI.getById(id),
          appointmentsAPI.getByPatient(id),
          messagesAPI.getConversation(id)
        ]);
        
        setPatient(patientRes.data);
        setAppointments(appointmentsRes.data);
        setMessages(messagesRes.data);
        
      } catch (err) {
        console.error('Error fetching patient data:', err);
        setError('Failed to load patient data');
      } finally {
        setLoading(false);
      }
    };
    
    fetchPatientData();
  }, [id]);
  
  // Format date
  const formatDate = (dateString: string) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString();
  };
  
  // Format datetime for messages
  const formatMessageTime = (dateString: string) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  if (loading) return <div className="text-center p-5">Loading patient data...</div>;
  if (error) return <div className="alert alert-danger m-3">{error}</div>;
  if (!patient) return <div className="alert alert-warning m-3">Patient not found</div>;
  
  return (
    <Container>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h1>Patient Profile</h1>
        <Link to="/patients" className="btn btn-outline-primary">
          Back to Patients
        </Link>
      </div>
      
      <Row>
        {/* Patient Information Card */}
        <Col lg={4} className="mb-4">
          <Card className="shadow-sm h-100">
            <Card.Header>
              <h5 className="mb-0">Personal Information</h5>
            </Card.Header>
            <Card.Body>
              <div className="text-center mb-4">
                <div className="display-6 mb-2">{patient.name}</div>
                <Badge bg="info" className="me-2">
                  {patient.language === 'en' ? 'English' : 
                   patient.language === 'sw' ? 'Swahili' : 
                   patient.language}
                </Badge>
                <Badge bg="secondary">
                  {`${patient.age} years, ${patient.gender}`}
                </Badge>
              </div>
              
              <ListGroup variant="flush">
                <ListGroup.Item>
                  <strong>Phone:</strong> {patient.phone_number}
                </ListGroup.Item>
                <ListGroup.Item>
                  <strong>Location:</strong> {patient.location}
                </ListGroup.Item>
                <ListGroup.Item>
                  <strong>Registered:</strong> {formatDate(patient.created_at)}
                </ListGroup.Item>
              </ListGroup>
            </Card.Body>
            <Card.Footer>
              <div className="d-grid gap-2">
                <Link to={`/messages/${patient.id}`} className="btn btn-primary">
                  Send Message
                </Link>
              </div>
            </Card.Footer>
          </Card>
        </Col>
        
        {/* Tabs for Appointments, Messages, and Symptoms */}
        <Col lg={8}>
          <Card className="shadow-sm">
            <Card.Header>
              <h5 className="mb-0">Patient History</h5>
            </Card.Header>
            <Card.Body>
              <Tab.Container defaultActiveKey="appointments">
                <Nav variant="tabs" className="mb-3">
                  <Nav.Item>
                    <Nav.Link eventKey="appointments">
                      Appointments
                      {appointments.length > 0 && (
                        <Badge bg="secondary" className="ms-2">
                          {appointments.length}
                        </Badge>
                      )}
                    </Nav.Link>
                  </Nav.Item>
                  <Nav.Item>
                    <Nav.Link eventKey="messages">
                      Messages
                      {messages.length > 0 && (
                        <Badge bg="secondary" className="ms-2">
                          {messages.length}
                        </Badge>
                      )}
                    </Nav.Link>
                  </Nav.Item>
                  <Nav.Item>
                    <Nav.Link eventKey="symptoms">
                      Symptoms
                      {patient.symptoms && patient.symptoms.length > 0 && (
                        <Badge bg="secondary" className="ms-2">
                          {patient.symptoms.length}
                        </Badge>
                      )}
                    </Nav.Link>
                  </Nav.Item>
                </Nav>
                
                <Tab.Content>
                  {/* Appointments Tab */}
                  <Tab.Pane eventKey="appointments">
                    {appointments.length > 0 ? (
                      <ListGroup variant="flush">
                        {appointments.map((appointment) => (
                          <ListGroup.Item key={appointment.id}>
                            <div className="d-flex justify-content-between align-items-center">
                              <div>
                                <div>
                                  <strong>Date:</strong> {appointment.date} at {appointment.time}
                                </div>
                                {appointment.notes && (
                                  <div className="mt-2">
                                    <strong>Notes:</strong> {appointment.notes}
                                  </div>
                                )}
                              </div>
                              <Badge bg={
                                appointment.status === 'confirmed' ? 'success' :
                                appointment.status === 'pending' ? 'warning' :
                                appointment.status === 'cancelled' ? 'danger' : 'secondary'
                              }>
                                {appointment.status}
                              </Badge>
                            </div>
                          </ListGroup.Item>
                        ))}
                      </ListGroup>
                    ) : (
                      <p className="text-center py-3">No appointments found for this patient</p>
                    )}
                  </Tab.Pane>
                  
                  {/* Messages Tab */}
                  <Tab.Pane eventKey="messages">
                    {messages.length > 0 ? (
                      <div className="message-list p-3">
                        {messages.map((message) => (
                          <div 
                            key={message.id} 
                            className={`message-bubble ${
                              message.sender_type === 'provider' 
                                ? 'message-from-provider' 
                                : 'message-from-patient'
                            }`}
                          >
                            <div>{message.content}</div>
                            <div className="message-time">
                              {formatMessageTime(message.created_at)}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-center py-3">No messages exchanged with this patient</p>
                    )}
                    <div className="text-center mt-3">
                      <Link to={`/messages/${patient.id}`} className="btn btn-primary">
                        Open Full Conversation
                      </Link>
                    </div>
                  </Tab.Pane>
                  
                  {/* Symptoms Tab */}
                  <Tab.Pane eventKey="symptoms">
                    {patient.symptoms && patient.symptoms.length > 0 ? (
                      <ListGroup variant="flush">
                        {patient.symptoms.map((symptom, index) => (
                          <ListGroup.Item key={index}>
                            {symptom}
                          </ListGroup.Item>
                        ))}
                      </ListGroup>
                    ) : (
                      <p className="text-center py-3">No symptoms reported by this patient</p>
                    )}
                  </Tab.Pane>
                </Tab.Content>
              </Tab.Container>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default PatientDetail;