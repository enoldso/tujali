import React, { useState, useEffect } from 'react';
import { 
  Container, Table, Card, Form, InputGroup, 
  Button, Badge, Pagination
} from 'react-bootstrap';
import { Link } from 'react-router-dom';
import { patientsAPI } from '../services/api';

interface Patient {
  id: string;
  name: string;
  phone_number: string;
  age: number;
  gender: string;
  location: string;
  language: string;
  created_at: string;
}

const Patients: React.FC = () => {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [filteredPatients, setFilteredPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState<string>('');
  
  // Pagination
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [patientsPerPage] = useState<number>(10);
  
  useEffect(() => {
    const fetchPatients = async () => {
      try {
        setLoading(true);
        const response = await patientsAPI.getAll();
        setPatients(response.data);
        setFilteredPatients(response.data);
      } catch (err) {
        console.error('Error fetching patients:', err);
        setError('Failed to load patients data');
      } finally {
        setLoading(false);
      }
    };
    
    fetchPatients();
  }, []);
  
  // Search/filter patients
  useEffect(() => {
    const results = patients.filter(patient => 
      patient.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      patient.phone_number.includes(searchTerm) ||
      patient.location.toLowerCase().includes(searchTerm.toLowerCase())
    );
    setFilteredPatients(results);
    setCurrentPage(1); // Reset to first page when search changes
  }, [searchTerm, patients]);
  
  // Format date
  const formatDate = (dateString: string) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString();
  };
  
  // Get current patients for pagination
  const indexOfLastPatient = currentPage * patientsPerPage;
  const indexOfFirstPatient = indexOfLastPatient - patientsPerPage;
  const currentPatients = filteredPatients.slice(indexOfFirstPatient, indexOfLastPatient);
  
  // Calculate total pages
  const totalPages = Math.ceil(filteredPatients.length / patientsPerPage);
  
  // Change page
  const paginate = (pageNumber: number) => setCurrentPage(pageNumber);

  if (loading) return <div className="text-center p-5">Loading patients data...</div>;
  if (error) return <div className="alert alert-danger m-3">{error}</div>;
  
  return (
    <Container>
      <h1 className="mb-4">Patients</h1>
      
      <Card className="mb-4 shadow-sm">
        <Card.Body>
          <Form>
            <InputGroup>
              <Form.Control
                placeholder="Search by name, phone number, or location"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
              {searchTerm && (
                <Button 
                  variant="outline-secondary" 
                  onClick={() => setSearchTerm('')}
                >
                  Clear
                </Button>
              )}
            </InputGroup>
          </Form>
        </Card.Body>
      </Card>
      
      <Card className="shadow-sm">
        <Card.Body>
          <Table responsive hover>
            <thead>
              <tr>
                <th>Name</th>
                <th>Phone Number</th>
                <th>Age</th>
                <th>Gender</th>
                <th>Location</th>
                <th>Language</th>
                <th>Registered</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {currentPatients.length > 0 ? (
                currentPatients.map((patient) => (
                  <tr key={patient.id}>
                    <td>{patient.name}</td>
                    <td>{patient.phone_number}</td>
                    <td>{patient.age}</td>
                    <td>{patient.gender}</td>
                    <td>{patient.location}</td>
                    <td>
                      <Badge bg="info">
                        {patient.language === 'en' ? 'English' : 
                         patient.language === 'sw' ? 'Swahili' : 
                         patient.language}
                      </Badge>
                    </td>
                    <td>{formatDate(patient.created_at)}</td>
                    <td>
                      <Link 
                        to={`/patients/${patient.id}`} 
                        className="btn btn-sm btn-primary"
                      >
                        View
                      </Link>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={8} className="text-center py-3">
                    {searchTerm ? 'No patients match your search criteria' : 'No patients found'}
                  </td>
                </tr>
              )}
            </tbody>
          </Table>
          
          {/* Pagination */}
          {totalPages > 1 && (
            <div className="d-flex justify-content-center mt-4">
              <Pagination>
                <Pagination.First 
                  onClick={() => paginate(1)} 
                  disabled={currentPage === 1}
                />
                <Pagination.Prev 
                  onClick={() => paginate(currentPage - 1)}
                  disabled={currentPage === 1}
                />
                
                {[...Array(totalPages)].map((_, index) => {
                  const pageNum = index + 1;
                  // Show current page, first/last page, and pages near current page
                  if (
                    pageNum === 1 || 
                    pageNum === totalPages || 
                    (pageNum >= currentPage - 1 && pageNum <= currentPage + 1)
                  ) {
                    return (
                      <Pagination.Item
                        key={pageNum}
                        active={pageNum === currentPage}
                        onClick={() => paginate(pageNum)}
                      >
                        {pageNum}
                      </Pagination.Item>
                    );
                  } else if (
                    pageNum === currentPage - 2 || 
                    pageNum === currentPage + 2
                  ) {
                    return <Pagination.Ellipsis key={pageNum} />;
                  }
                  return null;
                })}
                
                <Pagination.Next 
                  onClick={() => paginate(currentPage + 1)}
                  disabled={currentPage === totalPages}
                />
                <Pagination.Last 
                  onClick={() => paginate(totalPages)}
                  disabled={currentPage === totalPages}
                />
              </Pagination>
            </div>
          )}
        </Card.Body>
      </Card>
    </Container>
  );
};

export default Patients;