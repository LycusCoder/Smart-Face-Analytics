import React, { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import { Camera, Upload, BarChart3, Users, Clock, Brain, Eye, Smile, Zap, Play, Square, RotateCcw } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Badge } from './components/ui/badge';
import { Progress } from './components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Alert, AlertDescription } from './components/ui/alert';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [activeTab, setActiveTab] = useState('camera');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [results, setResults] = useState(null);
  const [history, setHistory] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [error, setError] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [stream, setStream] = useState(null);
  
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const fileInputRef = useRef(null);
  
  const sessionId = useRef(generateSessionId()).current;

  function generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  // Initialize camera
  const startCamera = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({ 
        video: { width: 640, height: 480 } 
      });
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
        setStream(mediaStream);
        setIsRecording(true);
      }
    } catch (err) {
      setError('Camera access denied. Please allow camera permissions.');
      console.error('Camera error:', err);
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
      setIsRecording(false);
    }
  };

  // Capture image from camera
  const captureImage = () => {
    if (!videoRef.current) return null;
    
    const canvas = canvasRef.current;
    const video = videoRef.current;
    const ctx = canvas.getContext('2d');
    
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0);
    
    return canvas.toDataURL('image/jpeg', 0.8);
  };

  // Analyze captured image
  const analyzeCapture = async () => {
    const imageData = captureImage();
    if (!imageData) {
      setError('Failed to capture image');
      return;
    }
    
    await analyzeImage(imageData);
  };

  // Analyze image (from camera or upload)
  const analyzeImage = async (imageData) => {
    if (!imageData) return;
    
    setIsAnalyzing(true);
    setError('');
    
    try {
      const base64Data = imageData.split(',')[1]; // Remove data:image/jpeg;base64, prefix
      
      const response = await axios.post(`${API}/analyze-image`, {
        image_data: base64Data,
        session_id: sessionId
      });
      
      setResults(response.data);
      await fetchHistory(); // Refresh history
      await fetchAnalytics(); // Refresh analytics
      
    } catch (err) {
      setError('Analysis failed: ' + (err.response?.data?.detail || err.message));
      console.error('Analysis error:', err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Handle file upload
  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    if (!file.type.startsWith('image/')) {
      setError('Please select an image file');
      return;
    }
    
    const reader = new FileReader();
    reader.onload = (e) => {
      analyzeImage(e.target.result);
    };
    reader.readAsDataURL(file);
  };

  // Fetch analysis history
  const fetchHistory = async () => {
    try {
      const response = await axios.get(`${API}/analysis-history?session_id=${sessionId}`);
      setHistory(response.data);
    } catch (err) {
      console.error('Failed to fetch history:', err);
    }
  };

  // Fetch analytics
  const fetchAnalytics = async () => {
    try {
      const response = await axios.get(`${API}/analytics/summary?session_id=${sessionId}`);
      setAnalytics(response.data);
    } catch (err) {
      console.error('Failed to fetch analytics:', err);
    }
  };

  // Initialize data on mount
  useEffect(() => {
    fetchHistory();
    fetchAnalytics();
  }, []);

  // Cleanup camera on unmount
  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  const resetSession = async () => {
    try {
      await axios.delete(`${API}/analysis-history?session_id=${sessionId}`);
      setResults(null);
      setHistory([]);
      setAnalytics(null);
      await fetchAnalytics();
    } catch (err) {
      console.error('Failed to reset session:', err);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <Brain className="h-12 w-12 text-blue-400 mr-3" />
            <h1 className="text-4xl font-bold text-white">Smart Face Analytics</h1>
          </div>
          <p className="text-slate-300 text-lg">Real-time AI Face Analysis dengan deteksi usia, ras, dan emosi</p>
          <Badge variant="outline" className="mt-2 bg-blue-500/10 text-blue-300 border-blue-400">
            Powered by HuggingFace & MediaPipe
          </Badge>
        </div>

        {/* Error Alert */}
        {error && (
          <Alert className="mb-6 bg-red-500/10 border-red-500 text-red-200">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Main Content */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-3 bg-slate-800 border-slate-700">
            <TabsTrigger 
              value="camera" 
              className="data-[state=active]:bg-blue-600 data-[state=active]:text-white"
              data-testid="camera-tab"
            >
              <Camera className="h-4 w-4 mr-2" />
              Real-time Camera
            </TabsTrigger>
            <TabsTrigger 
              value="upload" 
              className="data-[state=active]:bg-blue-600 data-[state=active]:text-white"
              data-testid="upload-tab"
            >
              <Upload className="h-4 w-4 mr-2" />
              Upload Image
            </TabsTrigger>
            <TabsTrigger 
              value="analytics" 
              className="data-[state=active]:bg-blue-600 data-[state=active]:text-white"
              data-testid="analytics-tab"
            >
              <BarChart3 className="h-4 w-4 mr-2" />
              Analytics
            </TabsTrigger>
          </TabsList>

          {/* Camera Tab */}
          <TabsContent value="camera" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Camera Feed */}
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-white flex items-center">
                    <Eye className="h-5 w-5 mr-2" />
                    Camera Feed
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="relative">
                    <video
                      ref={videoRef}
                      autoPlay
                      playsInline
                      muted
                      className="w-full h-64 bg-slate-700 rounded-lg object-cover"
                      data-testid="camera-video"
                    />
                    <canvas ref={canvasRef} className="hidden" />
                    
                    {/* Camera Controls */}
                    <div className="flex justify-center space-x-3 mt-4">
                      {!isRecording ? (
                        <Button 
                          onClick={startCamera} 
                          className="bg-green-600 hover:bg-green-700"
                          data-testid="start-camera-btn"
                        >
                          <Play className="h-4 w-4 mr-2" />
                          Start Camera
                        </Button>
                      ) : (
                        <Button 
                          onClick={stopCamera} 
                          variant="destructive"
                          data-testid="stop-camera-btn"
                        >
                          <Square className="h-4 w-4 mr-2" />
                          Stop Camera
                        </Button>
                      )}
                      
                      <Button
                        onClick={analyzeCapture}
                        disabled={!isRecording || isAnalyzing}
                        className="bg-blue-600 hover:bg-blue-700"
                        data-testid="analyze-capture-btn"
                      >
                        <Zap className="h-4 w-4 mr-2" />
                        {isAnalyzing ? 'Analyzing...' : 'Analyze Frame'}
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Results Panel */}
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-white">Analysis Results</CardTitle>
                  <CardDescription className="text-slate-300">
                    Real-time face analysis results
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {isAnalyzing && (
                    <div className="text-center py-8">
                      <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
                      <p className="text-slate-300">Analyzing faces...</p>
                    </div>
                  )}

                  {results && !isAnalyzing && (
                    <div className="space-y-4" data-testid="analysis-results">
                      <div className="flex justify-between items-center">
                        <span className="text-slate-300">Faces Detected:</span>
                        <Badge className="bg-green-600">{results.faces_detected}</Badge>
                      </div>
                      
                      <div className="flex justify-between items-center">
                        <span className="text-slate-300">Processing Time:</span>
                        <Badge variant="outline" className="text-blue-300">
                          {results.processing_time_ms.toFixed(2)}ms
                        </Badge>
                      </div>

                      {results.results.map((face, index) => (
                        <div key={index} className="border border-slate-600 rounded-lg p-4 space-y-3">
                          <h4 className="text-white font-semibold">Face #{face.face_id}</h4>
                          
                          <div className="grid grid-cols-2 gap-4 text-sm">
                            <div>
                              <span className="text-slate-400">Age:</span>
                              <div className="text-white font-medium">{face.age.value} years</div>
                              <Progress value={face.age.confidence * 100} className="h-2" />
                            </div>
                            
                            <div>
                              <span className="text-slate-400">Confidence:</span>
                              <div className="text-white font-medium">{(face.confidence * 100).toFixed(1)}%</div>
                              <Progress value={face.confidence * 100} className="h-2" />
                            </div>
                            
                            <div>
                              <span className="text-slate-400">Race:</span>
                              <div className="text-white font-medium">{face.race.value}</div>
                              <Progress value={face.race.confidence * 100} className="h-2" />
                            </div>
                            
                            <div>
                              <span className="text-slate-400">Emotion:</span>
                              <div className="flex items-center">
                                <Smile className="h-4 w-4 mr-1 text-yellow-400" />
                                <span className="text-white font-medium">{face.emotion.value}</span>
                              </div>
                              <Progress value={face.emotion.confidence * 100} className="h-2" />
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {!results && !isAnalyzing && (
                    <div className="text-center py-8 text-slate-400">
                      <Brain className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>Start camera dan capture frame untuk analisis</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Upload Tab */}
          <TabsContent value="upload" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Upload Area */}
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-white flex items-center">
                    <Upload className="h-5 w-5 mr-2" />
                    Upload Image
                  </CardTitle>
                  <CardDescription className="text-slate-300">
                    Upload gambar untuk analisis face detection
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div
                      className="border-2 border-dashed border-slate-600 rounded-lg p-8 text-center hover:border-blue-500 transition-colors cursor-pointer"
                      onClick={() => fileInputRef.current?.click()}
                      data-testid="upload-area"
                    >
                      <Upload className="h-12 w-12 mx-auto mb-4 text-slate-400" />
                      <p className="text-slate-300 mb-2">Click untuk upload gambar</p>
                      <p className="text-slate-500 text-sm">Mendukung JPG, PNG, WebP</p>
                    </div>
                    
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/*"
                      onChange={handleFileUpload}
                      className="hidden"
                      data-testid="file-input"
                    />
                    
                    <Button
                      onClick={() => fileInputRef.current?.click()}
                      className="w-full bg-blue-600 hover:bg-blue-700"
                      disabled={isAnalyzing}
                      data-testid="upload-btn"
                    >
                      <Upload className="h-4 w-4 mr-2" />
                      {isAnalyzing ? 'Analyzing...' : 'Choose File'}
                    </Button>
                  </div>
                </CardContent>
              </Card>

              {/* Upload Results */}
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-white">Upload Results</CardTitle>
                </CardHeader>
                <CardContent>
                  {isAnalyzing && (
                    <div className="text-center py-8">
                      <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
                      <p className="text-slate-300">Processing image...</p>
                    </div>
                  )}

                  {results && !isAnalyzing && (
                    <div className="space-y-4">
                      <div className="text-center mb-4">
                        <Badge className="bg-green-600 text-white">
                          ✓ Analysis Complete
                        </Badge>
                      </div>
                      
                      {results.results.map((face, index) => (
                        <div key={index} className="bg-slate-700 rounded-lg p-4 space-y-3">
                          <h4 className="text-white font-semibold flex items-center">
                            <Users className="h-4 w-4 mr-2" />
                            Face #{face.face_id}
                          </h4>
                          
                          <div className="grid grid-cols-1 gap-3 text-sm">
                            <div className="flex justify-between">
                              <span className="text-slate-400">Estimated Age:</span>
                              <span className="text-white font-medium">{face.age.value} years</span>
                            </div>
                            
                            <div className="flex justify-between">
                              <span className="text-slate-400">Ethnicity:</span>
                              <span className="text-white font-medium">{face.race.value}</span>
                            </div>
                            
                            <div className="flex justify-between">
                              <span className="text-slate-400">Emotion:</span>
                              <span className="text-white font-medium">{face.emotion.value}</span>
                            </div>
                            
                            <div className="flex justify-between">
                              <span className="text-slate-400">Detection Confidence:</span>
                              <span className="text-white font-medium">{(face.confidence * 100).toFixed(1)}%</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {!results && !isAnalyzing && (
                    <div className="text-center py-8 text-slate-400">
                      <Upload className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>Upload gambar untuk memulai analisis</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Analytics Tab */}
          <TabsContent value="analytics" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-white">Analytics Dashboard</h2>
              <Button 
                onClick={resetSession} 
                variant="outline"
                className="border-red-500 text-red-400 hover:bg-red-500 hover:text-white"
                data-testid="reset-session-btn"
              >
                <RotateCcw className="h-4 w-4 mr-2" />
                Reset Session
              </Button>
            </div>

            {/* Analytics Summary */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card className="bg-slate-800 border-slate-700">
                <CardContent className="p-6">
                  <div className="flex items-center space-x-2">
                    <Users className="h-8 w-8 text-blue-400" />
                    <div>
                      <p className="text-slate-400 text-sm">Total Faces</p>
                      <p className="text-2xl font-bold text-white" data-testid="total-faces">
                        {analytics?.total_faces || 0}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-slate-800 border-slate-700">
                <CardContent className="p-6">
                  <div className="flex items-center space-x-2">
                    <BarChart3 className="h-8 w-8 text-green-400" />
                    <div>
                      <p className="text-slate-400 text-sm">Analyses</p>
                      <p className="text-2xl font-bold text-white" data-testid="total-analyses">
                        {analytics?.total_analyses || 0}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-slate-800 border-slate-700">
                <CardContent className="p-6">
                  <div className="flex items-center space-x-2">
                    <Clock className="h-8 w-8 text-yellow-400" />
                    <div>
                      <p className="text-slate-400 text-sm">Avg Age</p>
                      <p className="text-2xl font-bold text-white" data-testid="avg-age">
                        {analytics?.avg_age || 0}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-slate-800 border-slate-700">
                <CardContent className="p-6">
                  <div className="flex items-center space-x-2">
                    <Zap className="h-8 w-8 text-purple-400" />
                    <div>
                      <p className="text-slate-400 text-sm">Avg Speed</p>
                      <p className="text-2xl font-bold text-white" data-testid="avg-processing-time">
                        {analytics?.avg_processing_time?.toFixed(0) || 0}ms
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Distributions */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Emotion Distribution */}
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-white flex items-center">
                    <Smile className="h-5 w-5 mr-2" />
                    Emotion Distribution
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {analytics?.emotion_distribution && Object.keys(analytics.emotion_distribution).length > 0 ? (
                    <div className="space-y-3">
                      {Object.entries(analytics.emotion_distribution).map(([emotion, count]) => (
                        <div key={emotion} className="flex items-center justify-between">
                          <span className="text-slate-300">{emotion}</span>
                          <div className="flex items-center space-x-2">
                            <div className="w-24 bg-slate-600 rounded-full h-2">
                              <div 
                                className="bg-blue-500 h-2 rounded-full"
                                style={{ width: `${(count / analytics.total_faces) * 100}%` }}
                              ></div>
                            </div>
                            <span className="text-white font-medium">{count}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-slate-400 text-center py-4">No emotion data available</p>
                  )}
                </CardContent>
              </Card>

              {/* Race Distribution */}
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-white flex items-center">
                    <Users className="h-5 w-5 mr-2" />
                    Ethnicity Distribution
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {analytics?.race_distribution && Object.keys(analytics.race_distribution).length > 0 ? (
                    <div className="space-y-3">
                      {Object.entries(analytics.race_distribution).map(([race, count]) => (
                        <div key={race} className="flex items-center justify-between">
                          <span className="text-slate-300">{race}</span>
                          <div className="flex items-center space-x-2">
                            <div className="w-24 bg-slate-600 rounded-full h-2">
                              <div 
                                className="bg-green-500 h-2 rounded-full"
                                style={{ width: `${(count / analytics.total_faces) * 100}%` }}
                              ></div>
                            </div>
                            <span className="text-white font-medium">{count}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-slate-400 text-center py-4">No ethnicity data available</p>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Recent History */}
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">Recent Analysis History</CardTitle>
              </CardHeader>
              <CardContent>
                {history.length > 0 ? (
                  <div className="space-y-3" data-testid="analysis-history">
                    {history.slice(0, 10).map((item, index) => (
                      <div key={item.id} className="flex items-center justify-between p-3 bg-slate-700 rounded-lg">
                        <div className="flex items-center space-x-3">
                          <Badge className="bg-blue-600">{item.faces_count} faces</Badge>
                          <span className="text-slate-300">Avg Age: {item.avg_age.toFixed(1)}</span>
                        </div>
                        <div className="text-right">
                          <p className="text-slate-400 text-sm">
                            {new Date(item.timestamp).toLocaleTimeString()}
                          </p>
                          <p className="text-slate-500 text-xs">
                            {item.processing_time_ms.toFixed(2)}ms
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-slate-400 text-center py-4">No analysis history available</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

export default App;