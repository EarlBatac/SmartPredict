import React, { useState, useEffect } from 'react';
import { Container, Tabs, Tab, Card, Row, Col, Alert, Form, Table, Badge, Spinner, Button } from 'react-bootstrap';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import 'bootstrap/dist/css/bootstrap.min.css';

function LoginPage({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  const handleLogin = (e) => {
    e.preventDefault();
    setError('');
    setIsLoggingIn(true);
    setTimeout(() => {
      if (username.trim() === 'admin' && password === 'password123') {
        onLogin();
      } else {
        setError('Invalid username or password.');
        setIsLoggingIn(false);
      }
    }, 1500);
  };

  return (
    <Container fluid className="d-flex align-items-center justify-content-center min-vh-100 bg-light">
      <Card className="p-5 border-0 shadow-lg" style={{ width: '100%', maxWidth: '450px', borderRadius: '15px' }}>
        <div className="text-center mb-4">
          <div className="bg-primary text-white rounded-circle d-inline-flex align-items-center justify-content-center mb-3 shadow" style={{ width: '60px', height: '60px' }}>
            <span className="fs-3 fw-bold">SP</span>
          </div>
          <h3 className="fw-bold text-dark mb-1">SmartPredict</h3>
          <p className="text-muted small">Login Page</p>
        </div>
        {error && <Alert variant="danger" className="small py-2 text-center">{error}</Alert>}
        <Form onSubmit={handleLogin}>
          <Form.Group className="mb-3">
            <Form.Label className="small fw-bold text-muted">Enter Username</Form.Label>
            <Form.Control type="text" placeholder="Enter username" value={username} onChange={(e) => setUsername(e.target.value)} required className="py-2" />
          </Form.Group>
          <Form.Group className="mb-4">
            <Form.Label className="small fw-bold text-muted">Enter Password</Form.Label>
            <Form.Control type="password" placeholder="Enter password" value={password} onChange={(e) => setPassword(e.target.value)} required className="py-2" />
          </Form.Group>
          <Button variant="primary" type="submit" className="w-100 py-2 fw-bold mb-3 shadow-sm" disabled={isLoggingIn}>
            {isLoggingIn ? <Spinner as="span" animation="border" size="sm" role="status" aria-hidden="true" /> : 'Login'}
          </Button>
        </Form>
      </Card>
    </Container>
  );
}

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [key, setKey] = useState('overview');
  const [category, setCategory] = useState('Daily');
  const [dashData, setDashData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!isAuthenticated) return;
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`http://127.0.0.1:5000/api/dashboard-data?category=${category}`);
        if (!response.ok) throw new Error("Server Error");
        const data = await response.json();
        setDashData(data);
      } catch (err) {
        setError("Failed to connect to AI backend. Ensure app.py is running.");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [category, isAuthenticated]);

  const handleLogout = () => {
    setIsAuthenticated(false);
    setDashData(null);
  };

  if (!isAuthenticated) return <LoginPage onLogin={() => setIsAuthenticated(true)} />;
  if (loading || !dashData) return <Container className="p-5 text-center"><Spinner animation="border" variant="primary" /><p className="mt-3">Loading SmartPredict Dashboard.....</p></Container>;
  if (error) return <Container className="p-5"><Alert variant="danger">{error}</Alert></Container>;

  return (
    <Container fluid className="p-4 bg-light min-vh-100">
      <header className="mb-4 d-flex justify-content-between align-items-center">
        <div>
          <h2 className="fw-bold text-primary mb-0">
            <span className="bg-primary text-white rounded px-2 py-1 me-2 fs-4 shadow-sm">SP</span>
            SmartPredict | AI ERP Dashboard
          </h2>
        </div>
        <div className="d-flex align-items-center gap-3">
          <Card className="p-2 border-0 shadow-sm">
            <Form.Select value={category} onChange={(e) => setCategory(e.target.value)} className="fw-bold text-dark">
              <option value="Daily">Daily Category</option>
              <option value="Seasonal">Seasonal Category</option>
              <option value="Occasional">Occasional Category</option>
              <option value="Top Selling">Top Selling Category</option>
            </Form.Select>
          </Card>
          <Button variant="outline-danger" onClick={handleLogout} className="fw-bold shadow-sm">Logout</Button>
        </div>
      </header>
      <Tabs activeKey={key} onSelect={(k) => setKey(k)} className="mb-4 custom-tabs">
        <Tab eventKey="overview" title="Executive Overview" />
        <Tab eventKey="demand" title="AI Prediction" />
        <Tab eventKey="suppliers" title="Supplier Analysis" />
      </Tabs>
      {key === 'overview' && (
        <div>
          <Alert variant="info" className="border-0 shadow-sm mb-4">
            <h6 className="fw-bold text-dark mb-1">Product Node Clarity:</h6>
            <p className="small text-dark mb-0">{dashData.stats.general_node_explanation}</p>
          </Alert>
          <Row className="g-4">
            <Col md={5}>
              <Card className="p-4 border-0 shadow-sm h-100">
                <h6 className="text-muted fw-bold">7-Day Demand Prediction: {dashData.stats.predicted_total} Units</h6>
                <div className="mb-3">
                   <Alert variant={dashData.stats.rec_color} className="fw-bold py-2">
                      {dashData.stats.recommendation}
                   </Alert>
                </div>
                <Table size="sm" borderless hover>
                  <tbody>
                    {dashData.breakdown?.map((item, i) => (
                      <tr key={i} className="border-bottom">
                        <td className="text-truncate" style={{maxWidth: '220px'}} title={item.name}>{item.name}</td>
                        <td className="text-end fw-bold text-primary">+{item.qty} units</td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              </Card>
            </Col>
            <Col md={7}>
              <Card className="p-4 border-0 shadow-sm h-100 bg-white">
                <h6 className="text-muted fw-bold mb-3">Trending Product Overview:</h6>
                <h5 className="fw-bold text-dark">{dashData.stats.trending_item}</h5>
                <Badge bg="primary" className="mb-3 px-3 py-2">{dashData.stats.category_definition}</Badge>
                <div className="bg-light p-3 rounded mb-3 border-start border-4 border-primary">
                  <p className="small text-dark mb-1 fw-bold">Trending Product Justification:</p>
                  <p className="small text-muted mb-0">{dashData.stats.result_justification}</p>
                </div>
                <p className="small text-dark mb-1 fw-bold">Trending Product Location:</p>
                <p className="small text-muted mb-0">{dashData.stats.trending_location}</p>
              </Card>
            </Col>
          </Row>
        </div>
      )}
      {key === 'demand' && (
        <Row className="g-4">
          <Col md={7}>
            <Card className="p-4 border-0 shadow-sm mb-4">
              <div className="d-flex justify-content-between align-items-center mb-3">
                <h5 className="fw-bold mb-0">7-Day XGBoost Prediction</h5>
                <Badge bg="success" className="p-2 fs-6">Denoised Accuracy (WMAPE): {dashData.segment_accuracy}</Badge>
              </div>
              <div style={{ height: 300 }}>
                <ResponsiveContainer>
                  <LineChart data={dashData.line_data}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="actual" stroke="#adb5bd" strokeWidth={2} name="Historical Validation" />
                    <Line type="monotone" dataKey="predicted" stroke="#0d6efd" strokeWidth={3} name="AI Target Prediction" dot={{r: 5}} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </Card>
            <Card className="p-4 border-0 shadow-sm bg-light border-start border-4 border-success">
              <h6 className="fw-bold text-dark mb-2">AI Accuracy Score Justification:</h6>
              <p className="small text-muted mb-0">{dashData.stats.accuracy_context}</p>
            </Card>
          </Col>
          <Col md={5}>
            <Card className="p-4 border-0 shadow-sm h-100">
              <h5 className="fw-bold text-primary mb-3">Model Logic</h5>
              <hr />
              <p className="fw-bold mb-2 text-dark">Implemented Time-Series Features:</p>
              <ul className="small text-muted ps-3 mb-0">
                {dashData.dynamic_features?.map((f, i) => (
                  <li key={i} className="mb-2">
                    <strong className="text-dark">{f.name} ({f.weight}% weight):</strong> {f.desc}
                  </li>
                ))}
              </ul>
            </Card>
          </Col>
        </Row>
      )}
      {key === 'suppliers' && (
        <Card className="p-4 border-0 shadow-sm rounded-4">
          <h5 className="fw-bold mb-4">Supplier Performance Analysis</h5>
          <Table hover responsive className="align-middle">
            <thead className="table-light">
              <tr>
                <th style={{width: '25%'}}>Supply Provider</th>
                <th style={{width: '15%'}}>Calculated Volatility Score</th>
                <th style={{width: '15%'}}>Supplier Performance Status</th>
                <th style={{width: '45%'}}>AI Calculation</th>
              </tr>
            </thead>
            <tbody>
              {dashData.suppliers.map((s, i) => (
                <tr key={i}>
                  <td className="fw-bold">{s.name}</td>
                  <td><Badge bg="secondary" className="px-3 py-2 fs-6">{s.score}</Badge></td>
                  <td><Badge bg={s.status.includes('High') ? 'success' : s.status.includes('Medium') ? 'warning' : 'danger'} className="px-3 py-2">{s.status}</Badge></td>
                  <td className="small text-muted">{s.justification}</td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Card>
      )}
    </Container>
  );
}
export default App;

