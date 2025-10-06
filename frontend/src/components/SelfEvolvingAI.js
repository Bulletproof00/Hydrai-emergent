import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Brain, Zap, TrendingUp, Clock, Target, Database, Cpu, BarChart3, AlertCircle, CheckCircle, Loader, MessageSquare, Code, Send, Terminal, Settings } from 'lucide-react';

const SelfEvolvingAI = () => {
    const [evolutionStatus, setEvolutionStatus] = useState(null);
    const [evolutionHistory, setEvolutionHistory] = useState([]);
    const [latestReport, setLatestReport] = useState(null);
    const [isTriggering, setIsTriggering] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    
    // New states for coding features
    const [pluginStatus, setPluginStatus] = useState(null);
    const [chatMessages, setChatMessages] = useState([]);
    const [chatInput, setChatInput] = useState('');
    const [improvementRequest, setImprovementRequest] = useState('');
    const [isGeneratingCode, setIsGeneratingCode] = useState(false);
    const [isChatting, setIsChatting] = useState(false);
    const [activeTab, setActiveTab] = useState('overview');

    const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

    useEffect(() => {
        fetchEvolutionData();
        // Refresh data every 30 seconds
        const interval = setInterval(fetchEvolutionData, 30000);
        return () => clearInterval(interval);
    }, []);

    const fetchEvolutionData = async () => {
        try {
            const token = localStorage.getItem('token');
            const headers = { 'Authorization': `Bearer ${token}` };

            // Fetch evolution status
            const statusResponse = await axios.get(`${BACKEND_URL}/api/ai/evolution/status`, { headers });
            if (statusResponse.data.status === 'success') {
                setEvolutionStatus(statusResponse.data.evolution_status);
            }

            // Fetch evolution history
            const historyResponse = await axios.get(`${BACKEND_URL}/api/ai/evolution/history?limit=5`, { headers });
            if (historyResponse.data.status === 'success') {
                setEvolutionHistory(historyResponse.data.evolution_history);
            }

            // Fetch latest report
            const reportResponse = await axios.get(`${BACKEND_URL}/api/ai/evolution/report/latest`, { headers });
            if (reportResponse.data.status === 'success') {
                setLatestReport(reportResponse.data.latest_report);
            }

            // Fetch plugin status
            const pluginsResponse = await axios.get(`${BACKEND_URL}/api/ai/coding/plugins`, { headers });
            if (pluginsResponse.data.status === 'success') {
                setPluginStatus(pluginsResponse.data.plugin_status);
            }

            setError(null);
        } catch (err) {
            console.error('Evolution data fetch error:', err);
            setError('Fehler beim Laden der Evolution-Daten');
        } finally {
            setLoading(false);
        }
    };

    const triggerEvolution = async () => {
        try {
            setIsTriggering(true);
            const token = localStorage.getItem('token');
            const headers = { 'Authorization': `Bearer ${token}` };

            const response = await axios.post(`${BACKEND_URL}/api/ai/evolution/trigger`, {}, { headers });
            
            if (response.data.status === 'success') {
                // Refresh data after successful trigger
                setTimeout(fetchEvolutionData, 2000);
            } else {
                setError(response.data.message || 'Evolution-Trigger fehlgeschlagen');
            }
        } catch (err) {
            console.error('Evolution trigger error:', err);
            setError('Fehler beim Auslösen der Evolution');
        } finally {
            setIsTriggering(false);
        }
    };

    const generateCode = async () => {
        if (!improvementRequest.trim()) return;

        try {
            setIsGeneratingCode(true);
            const token = localStorage.getItem('token');
            const headers = { 'Authorization': `Bearer ${token}` };

            const response = await axios.post(`${BACKEND_URL}/api/ai/coding/generate`, {
                improvement_request: improvementRequest
            }, { headers });
            
            if (response.data.status === 'success') {
                // Add to chat messages
                setChatMessages(prev => [...prev, 
                    { role: 'user', content: `Code generieren: ${improvementRequest}` },
                    { role: 'assistant', content: `✅ Code erfolgreich generiert und getestet!\n\nDetails:\n${JSON.stringify(response.data.coding_result, null, 2)}` }
                ]);
                setImprovementRequest('');
                // Refresh plugin data
                setTimeout(fetchEvolutionData, 1000);
            } else {
                setError(response.data.message || 'Code-Generierung fehlgeschlagen');
            }
        } catch (err) {
            console.error('Code generation error:', err);
            setError('Fehler beim Generieren von Code');
        } finally {
            setIsGeneratingCode(false);
        }
    };

    const sendChatMessage = async () => {
        if (!chatInput.trim()) return;

        try {
            setIsChatting(true);
            const token = localStorage.getItem('token');
            const headers = { 'Authorization': `Bearer ${token}` };

            const userMessage = chatInput;
            setChatInput('');

            // Add user message immediately
            setChatMessages(prev => [...prev, { role: 'user', content: userMessage }]);

            const response = await axios.post(`${BACKEND_URL}/api/ai/evolution/chat`, {
                message: userMessage
            }, { headers });
            
            if (response.data.status === 'success') {
                // Add AI response
                setChatMessages(prev => [...prev, { role: 'assistant', content: response.data.ai_response }]);
            } else {
                setChatMessages(prev => [...prev, { role: 'assistant', content: 'Entschuldigung, es gab einen Fehler bei der Verarbeitung deiner Nachricht.' }]);
            }
        } catch (err) {
            console.error('Chat error:', err);
            setChatMessages(prev => [...prev, { role: 'assistant', content: 'Verbindungsfehler. Bitte versuche es erneut.' }]);
        } finally {
            setIsChatting(false);
        }
    };

    const formatTimestamp = (timestamp) => {
        if (!timestamp) return 'Unbekannt';
        return new Date(timestamp).toLocaleString('de-DE');
    };

    const getPerformanceColor = (score) => {
        if (score >= 0.8) return 'text-green-400';
        if (score >= 0.6) return 'text-yellow-400';
        return 'text-red-400';
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-64">
                <Loader className="animate-spin" size={32} />
                <span className="ml-2">Lade Evolution-Daten...</span>
            </div>
        );
    }

    return (
        <div className="self-evolving-ai-container">
            <div className="header-section">
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center">
                        <Brain className="w-8 h-8 text-purple-400 mr-3" />
                        <h2 className="text-2xl font-bold text-white">Self-Evolving AI System</h2>
                    </div>
                    <button 
                        onClick={triggerEvolution}
                        disabled={isTriggering}
                        className="btn-primary flex items-center"
                    >
                        {isTriggering ? (
                            <Loader className="animate-spin mr-2" size={16} />
                        ) : (
                            <Zap className="mr-2" size={16} />
                        )}
                        Evolution Starten
                    </button>
                </div>

                {error && (
                    <div className="error-banner">
                        <AlertCircle size={16} />
                        <span>{error}</span>
                    </div>
                )}
            </div>

            {/* Evolution Status Overview */}
            {evolutionStatus && (
                <div className="status-grid">
                    <div className="stat-card">
                        <div className="stat-header">
                            <Cpu className="w-5 h-5 text-blue-400" />
                            <span>Evolution Zyklen</span>
                        </div>
                        <div className="stat-value">{evolutionStatus.total_evolution_cycles || 0}</div>
                    </div>

                    <div className="stat-card">
                        <div className="stat-header">
                            <Target className="w-5 h-5 text-green-400" />
                            <span>Performance Score</span>
                        </div>
                        <div className={`stat-value ${getPerformanceColor(evolutionStatus.current_performance_score)}`}>
                            {((evolutionStatus.current_performance_score || 0) * 100).toFixed(1)}%
                        </div>
                    </div>

                    <div className="stat-card">
                        <div className="stat-header">
                            <Clock className="w-5 h-5 text-yellow-400" />
                            <span>Nächste Evolution</span>
                        </div>
                        <div className="stat-value text-sm">
                            {formatTimestamp(evolutionStatus.next_evolution_eta)}
                        </div>
                    </div>

                    <div className="stat-card">
                        <div className="stat-header">
                            <CheckCircle className="w-5 h-5 text-purple-400" />
                            <span>Status</span>
                        </div>
                        <div className="stat-value">
                            {evolutionStatus.evolution_enabled ? (
                                <span className="text-green-400">Aktiv</span>
                            ) : (
                                <span className="text-red-400">Inaktiv</span>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Latest Evolution Report */}
            {latestReport && (
                <div className="evolution-report-section">
                    <h3 className="section-title">
                        <BarChart3 className="w-5 h-5 mr-2" />
                        Neuester Evolutionsbericht (Zyklus #{latestReport.cycle_number})
                    </h3>
                    <div className="report-card">
                        <div className="report-header">
                            <span className="report-date">
                                {formatTimestamp(latestReport.timestamp)}
                            </span>
                        </div>
                        <div className="report-content">
                            <pre className="report-text">
                                {latestReport.report || 'Bericht wird generiert...'}
                            </pre>
                        </div>
                    </div>
                </div>
            )}

            {/* Evolution History */}
            {evolutionHistory.length > 0 && (
                <div className="evolution-history-section">
                    <h3 className="section-title">
                        <Database className="w-5 h-5 mr-2" />
                        Evolution Verlauf
                    </h3>
                    <div className="history-timeline">
                        {evolutionHistory.map((cycle, index) => (
                            <div key={cycle._id || index} className="timeline-item">
                                <div className="timeline-marker">
                                    <Brain size={12} />
                                </div>
                                <div className="timeline-content">
                                    <div className="timeline-header">
                                        <span className="cycle-number">Zyklus #{cycle.cycle_number}</span>
                                        <span className="cycle-date">{formatTimestamp(cycle.timestamp)}</span>
                                    </div>
                                    <div className="timeline-details">
                                        <div className="detail-item">
                                            <span className="detail-label">Dauer:</span>
                                            <span className="detail-value">{cycle.duration_seconds?.toFixed(1)}s</span>
                                        </div>
                                        {cycle.performance_analysis && (
                                            <div className="detail-item">
                                                <span className="detail-label">Performance:</span>
                                                <span className={`detail-value ${getPerformanceColor(cycle.performance_analysis.performance_score)}`}>
                                                    {(cycle.performance_analysis.performance_score * 100).toFixed(1)}%
                                                </span>
                                            </div>
                                        )}
                                        {cycle.algorithm_improvements && (
                                            <div className="detail-item">
                                                <span className="detail-label">Verbesserungen:</span>
                                                <span className="detail-value text-green-400">
                                                    {Object.keys(cycle.algorithm_improvements).length} implementiert
                                                </span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Evolution Capabilities */}
            <div className="capabilities-section">
                <h3 className="section-title">
                    <TrendingUp className="w-5 h-5 mr-2" />
                    KI-Fähigkeiten
                </h3>
                <div className="capabilities-grid">
                    <div className="capability-card">
                        <div className="capability-icon">
                            <Brain className="w-6 h-6 text-blue-400" />
                        </div>
                        <div className="capability-content">
                            <h4>Selbst-Analyse</h4>
                            <p>Analysiert eigene Performance und identifiziert Verbesserungspotentiale</p>
                        </div>
                    </div>

                    <div className="capability-card">
                        <div className="capability-icon">
                            <Database className="w-6 h-6 text-green-400" />
                        </div>
                        <div className="capability-content">
                            <h4>Daten-Optimierung</h4>
                            <p>Identifiziert fehlende Datenquellen für bessere Vorhersagen</p>
                        </div>
                    </div>

                    <div className="capability-card">
                        <div className="capability-icon">
                            <Cpu className="w-6 h-6 text-purple-400" />
                        </div>
                        <div className="capability-content">
                            <h4>Algorithmus-Evolution</h4>
                            <p>Entwickelt neue Berechnungsmethoden und optimiert Vorhersagemodelle</p>
                        </div>
                    </div>

                    <div className="capability-card">
                        <div className="capability-icon">
                            <Zap className="w-6 h-6 text-yellow-400" />
                        </div>
                        <div className="capability-content">
                            <h4>Kontinuierliches Lernen</h4>
                            <p>Lernt aus Erfolgen und Fehlern für kontinuierliche Verbesserung</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SelfEvolvingAI;