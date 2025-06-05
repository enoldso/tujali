import React, { useState, useEffect } from 'react';
import { 
  Container, Card, Table, Badge, Button, 
  Form, Row, Col, Modal, Dropdown
} from 'react-bootstrap';
import { Link } from 'react-router-dom';
import { appointmentsAPI } from '../services/api';

interface Appointment {
  id: string;
  patient_id: string;
  patient_name: string;
  provider_id: string;
  provider_name: string;
  date: string;
  time: string;
  status: string;
  notes: string;
  created_at: string;
}

const Appointments: React.FC = () => {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [filteredAppointments, setFilteredAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [dateFilter, setDateFilter] = useState<string>('');
  
  // Modal state for status update
  const [showModal, setShowModal] = useState<boolean>(false);
  const [selectedAppointment, setSelectedAppointment] = useState<Appointment | null>(null);
  const [newStatus, setNewStatus] = useState<string>('');
  const [updateLoading, setUpdateLoading] = useState<boolean>(false);
  
  useEffect(() => {
    const fetchAppointments = async () => {
      try {
        setLoading(true);
        const response = await appointmentsAPI.getAll();
        setAppointments(response.data);
        setFilteredAppointments(response.data);
      } catch (err) {
        console.error('Error fetching appointments:', err);
        setError('Failed to load appointments data');
      } finally {
        setLoading(false);
      }
    };
    
    fetchAppointments();
  }, []);
  
  // Apply filters
  useEffect(() => {
    let results = [...appointments];
    
    // Apply status filter
    if (statusFilter !== 'all') {
      results = results.filter(appointment => appointment.status === statusFilter);
    }
    
    // Apply date filter
    if (dateFilter) {
      results = results.filter(appointment => appointment.date === dateFilter);
    }
    
    setFilteredAppointments(results);
  }, [statusFilter, dateFilter, appointments]);
  
  // Handle status update
  const openStatusModal = (appointment: Appointment) => {
    setSelectedAppointment(appointment);
    setNewStatus(appointment.status);
    setShowModal(true);
  };
  
  const updateStatus = async () => {
    if (!selectedAppointment || !newStatus) return;
    
    try {
      setUpdateLoading(true);
      await appointmentsAPI.updateStatus(selectedAppointment.id, newStatus);
      
      // Update the appointment status in the state
      const updatedAppointments = appointments.map(appointment => 
        appointment.id === selectedAppointment.id 
          ? { ...appointment, status: newStatus } 
          : appointment
      );
      
      setAppointments(updatedAppointments);
      setShowModal(false);
    } catch (err) {
      console.error('Error updating appointment status:', err);
      alert('Failed to update appointment status');
    } finally {
      setUpdateLoading(false);
    }
  };
  
  // Clear all filters
  const clearFilters = () => {
    setStatusFilter('all');
    setDateFilter('');
  };
  
  // Get unique dates for the date filter
  const uniqueDates = Array.from(new Set(appointments.map(a => a.date))).sort();

  if (loading) return <div className="text-center p-5">Loading appointments data...</div>;
  if (error) return <div className="alert alert-danger m-3">{error}</div>;
  
  return (
    <Container>
      <h1 className="mb-4">Appointments</h1>
      
      {/* Filters */}
      <Card className="mb-4 shadow-sm">
        <Card.Body>
          <Row className="align-items-end">
            <Col md={4}>
              <Form.Group>
                <Form.Label>Filter by Status</Form.Label>
                <Form.Select 
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                >
                  <option value="all">All Statuses</option>
                  <option value="pending">Pending</option>
                  <option value="confirmed">Confirmed</option>
                  <option value="completed">Completed</option>
                  <option value="cancelled">Cancelled</option>
                </Form.Select>
              </Form.Group>
            </Col>
            
            <Col md={4}>
              <Form.Group>
                <Form.Label>Filter by Date</Form.Label>
                <Form.Select 
                  value={dateFilter}
                  onChange={(e) => setDateFilter(e.target.value)}
                >
                  <option value="">All Dates</option>
                  {uniqueDates.map(date => (
                    <option key={date} value={date}>{date}</option>
                  ))}
                </Form.Select>
              </Form.Group>
            </Col>
            
            <Col md={4} className="d-flex justify-content-end">
              <Button 
                variant="outline-secondary" 
                onClick={clearFilters}
                className="mb-3"
              >
                Clear Filters
              </Button>
            </Col>
          </Row>
        </Card.Body>
      </Card>
      
      {/* Appointments Table */}
      <Card className="shadow-sm">
        <Card.Body>
          <Table responsive hover>
            <thead>
              <tr>
                <th>Patient</th>
                <th>Date</th>
                <th>Time</th>
                <th>Status</th>
                <th>Notes</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredAppointments.length > 0 ? (
                filteredAppointments.map((appointment) => (
                  <tr key={appointment.id}>
                    <td>
                      <Link to={`/patients/${appointment.patient_id}`}>
                        {appointment.patient_name}
                      </Link>
                    </td>
                    <td>{appointment.date}</td>
                    <td>{appointment.time}</td>
                    <td>
                      <Badge bg={
                        appointment.status === 'confirmed' ? 'success' :
                        appointment.status === 'pending' ? 'warning' :
                        appointment.status === 'completed' ? 'info' :
                        appointment.status === 'cancelled' ? 'danger' : 'secondary'
                      }>
                        {appointment.status}
                      </Badge>
                    </td>
                    <td>
                      {appointment.notes 
                        ? appointment.notes.length > 50 
                          ? `${appointment.notes.substring(0, 50)}...` 
                          : appointment.notes 
                        : '-'
                      }
                    </td>
                    <td>
                      <Dropdown>
                        <Dropdown.Toggle variant="outline-secondary" size="sm">
                          Actions
                        </Dropdown.Toggle>
                        <Dropdown.Menu>
                          <Dropdown.Item 
                            as={Link} 
                            to={`/patients/${appointment.patient_id}`}
                          >
                            View Patient
                          </Dropdown.Item>
                          <Dropdown.Item 
                            as={Link} 
                            to={`/messages/${appointment.patient_id}`}
                          >
                            Message Patient
                          </Dropdown.Item>
                          <Dropdown.Divider />
                          <Dropdown.Item onClick={() => openStatusModal(appointment)}>
                            Update Status
                          </Dropdown.Item>
                        </Dropdown.Menu>
                      </Dropdown>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="text-center py-3">
                    No appointments match your filter criteria
                  </td>
                </tr>
              )}
            </tbody>
          </Table>
        </Card.Body>
      </Card>
      
      {/* Status Update Modal */}
      <Modal show={showModal} onHide={() => setShowModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Update Appointment Status</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {selectedAppointment && (
            <>
              <p>
                <strong>Patient:</strong> {selectedAppointment.patient_name}<br />
                <strong>Date:</strong> {selectedAppointment.date}<br />
                <strong>Time:</strong> {selectedAppointment.time}
              </p>
              
              <Form.Group>
                <Form.Label>Appointment Status</Form.Label>
                <Form.Select 
                  value={newStatus}
                  onChange={(e) => setNewStatus(e.target.value)}
                >
                  <option value="pending">Pending</option>
                  <option value="confirmed">Confirmed</option>
                  <option value="completed">Completed</option>
                  <option value="cancelled">Cancelled</option>
                </Form.Select>
              </Form.Group>
            </>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowModal(false)}>
            Cancel
          </Button>
          <Button 
            variant="primary" 
            onClick={updateStatus}
            disabled={updateLoading}
          >
            {updateLoading ? 'Updating...' : 'Update Status'}
          </Button>
        </Modal.Footer>
      </Modal>
    </Container>
  );
};

export default Appointments;