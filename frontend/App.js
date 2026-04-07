import React, { useState, useEffect } from 'react';
import { Tabs, Tab, Card, Table, Container, Row, Col, Alert } from 'react-bootstrap';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';
import 'bootstrap/dist/css/bootstrap.min.css';

function App() {
  const [key, setKey] = useState('overview');
  const [predictData, setPredictData] = useState([]);
  const [suppliers, setSuppliers] = useState([]);

  // Default simulated data for visualization if API is not yet connected
  const demoPredictions = [
    { time: 'Day 1', Daily: 400, Seasonal: 240, Occasional: 200 },
    { time: 'Day 2', Daily: 300, Seasonal: 139, Occasional: 221 },
    { time: 'Day 3', Daily: 200, Seasonal: 980, Occasional: 229 },
    { time: 'Day 4', Daily: 278, Seasonal: 390, Occasional: 200 },
  ];

  const demoSuppliers = [
    { name: "Global Electronics", score: 0.92, status: "Reliable" },
    { name: "TechComponents Ltd", score: 0.75, status: "Average" },
    { name: "FastTrack Parts", score: 0.45, status: "Low Performance" }
  ];

  return (
    <Container className="mt-4 shadow-sm p-4 bg-light rounded">
      <header className="mb-4 border-bottom pb-2">
        <h2 className="text-primary">SmartPredict: AI-Enhanced ERP</h2>
        <p className="text-muted">Electronic Retail Inventory & Supplier Management Prototype</p>
      </header>
      
      <Tabs activeKey={key} onSelect={(k) => setKey(k)} className="mb-4 nav-justified">
        
        {/* TAB 1: EXECUTIVE OVERVIEW */}
        <Tab eventKey="overview" title="Executive Overview">
          <Row className="g-4">
            <Col md={4}>
              <Card className="text-center border-primary">
                <Card.Body>
                  <Card.Title>JIT Inventory Margin</Card.Title>
                  <h3 className="text-success">±8.5%</h3>
                  <small className="text-muted">Target: ±10%</small>
                </Card.Body>
              </Card>
            </Col>
            <Col md={8}>
              <Alert variant="info">
                <strong>Recommendation:</strong> Based on upcoming <strong>Seasonal</strong> trends, increase stock for Laptop batteries by 15%.
              </Alert>
            </Col>
          </Row>
        </Tab>

        {/* TAB 2: DEMAND PREDICTION */}
        <Tab eventKey="demand" title="Demand Prediction">
          <Card className="p-3">
            <h4>Product Demand Forecasting (≥85% Accuracy)</h4>
            <p className="small text-muted">Categories: Daily, Seasonal, Occasional, Top Selling</p>
            <div style={{ width: '100%', height: 350 }}>
              <ResponsiveContainer>
                <LineChart data={demoPredictions}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="Daily" stroke="#007bff" strokeWidth={3} />
                  <Line type="monotone" dataKey="Seasonal" stroke="#ffc107" strokeWidth={3} />
                  <Line type="monotone" dataKey="Occasional" stroke="#28a745" strokeWidth={3} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </Tab>

        {/* TAB 3: SUPPLIER RELIABILITY */}
        <Tab eventKey="suppliers" title="Supplier Reliability">
          <Card className="p-3">
            <h4>Supplier Performance Metrics (≥80% F1 Score)</h4>
            <Table striped bordered hover responsive className="mt-3">
              <thead className="table-dark">
                <tr>
                  <th>Supplier Name</th>
                  <th>Reliability Score (0-1)</th>
                  <th>Categorization</th>
                </tr>
              </thead>
              <tbody>
                {demoSuppliers.map((s, idx) => (
                  <tr key={idx}>
                    <td>{s.name}</td>
                    <td>{s.score}</td>
                    <td>
                      <span className={`badge bg-${s.status === 'Reliable' ? 'success' : s.status === 'Average' ? 'warning' : 'danger'}`}>
                        {s.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </Card>
        </Tab>

      </Tabs>
    </Container>
  );
}

export default App; 
 
 
 
