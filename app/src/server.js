/**
 * FinCore Bank - Main Server
 * Express API with Swagger documentation
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const morgan = require('morgan');
const path = require('path');
const rateLimit = require('express-rate-limit');
require('dotenv').config();

const { testConnection } = require('./config/database');
const { setupSwagger } = require('./utils/swagger');
const { errorHandler } = require('./middleware/errorHandler');

// Import routes
const authRoutes = require('./routes/auth');
const customersRoutes = require('./routes/customers');
const accountsRoutes = require('./routes/accounts');
const transactionsRoutes = require('./routes/transactions');
const loansRoutes = require('./routes/loans');
const dashboardRoutes = require('./routes/dashboard');

// Initialize Express app
const app = express();

// Configuration
const API_PORT = process.env.API_PORT || 4000;
const UI_PORT = process.env.UI_PORT || 3000;
const NODE_ENV = process.env.NODE_ENV || 'development';
const allowedOrigins = (process.env.CORS_ORIGIN || 'http://localhost:3000,http://localhost:30000')
    .split(',')
    .map((origin) => origin.trim())
    .filter(Boolean);

// Security middleware
app.use(helmet({
    contentSecurityPolicy: false, // Disable for Swagger UI
}));

// Rate limiting
const limiter = rateLimit({
    windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS) || 15 * 60 * 1000, // 15 minutes
    max: parseInt(process.env.RATE_LIMIT_MAX_REQUESTS) || 100, // limit each IP to 100 requests per windowMs
    message: 'Too many requests from this IP, please try again later.'
});
app.use('/api/', limiter);

// CORS configuration
app.use(cors({
    origin: (origin, callback) => {
        if (!origin) {
            return callback(null, true);
        }

        if (allowedOrigins.includes(origin)) {
            return callback(null, true);
        }

        return callback(new Error(`Origin not allowed by CORS: ${origin}`), false);
    },
    credentials: true
}));

// Body parsing middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Compression middleware
app.use(compression());

// Logging middleware
if (NODE_ENV === 'development') {
    app.use(morgan('dev'));
} else {
    app.use(morgan('combined'));
}

// Setup Swagger documentation
setupSwagger(app);

// API Routes
app.use('/api/v1/auth', authRoutes);
app.use('/api/v1/customers', customersRoutes);
app.use('/api/v1/accounts', accountsRoutes);
app.use('/api/v1/transactions', transactionsRoutes);
app.use('/api/v1/loans', loansRoutes);
app.use('/api/v1/dashboard', dashboardRoutes);

// Health check endpoint
app.get('/api/v1/health', async (req, res) => {
    const dbConnected = await testConnection();
    res.json({
        status: 'ok',
        db: dbConnected ? 'connected' : 'disconnected',
        timestamp: new Date().toISOString(),
        version: '1.0.0',
        environment: NODE_ENV
    });
});

// Serve React static files in production
if (NODE_ENV === 'production') {
    const clientBuildPath = path.join(__dirname, '../client/build');
    app.use(express.static(clientBuildPath));
    
    // Serve React app for all non-API routes
    app.get('*', (req, res) => {
        if (!req.path.startsWith('/api')) {
            res.sendFile(path.join(clientBuildPath, 'index.html'));
        }
    });
}

// 404 handler for API routes
app.use('/api/*', (req, res) => {
    res.status(404).json({
        error: 'Endpoint not found',
        code: 'NOT_FOUND',
        path: req.path
    });
});

// Global error handler
app.use(errorHandler);

// Start server
const startServer = async () => {
    try {
        // Test database connection
        console.log('🔍 Testing database connection...');
        const dbConnected = await testConnection();
        
        if (!dbConnected) {
            console.error('❌ Failed to connect to database');
            console.error('   Check your .env configuration');
            process.exit(1);
        }
        
        // Start API server
        app.listen(API_PORT, () => {
            console.log('');
            console.log('================================================================');
            console.log('  FinCore Bank API Server');
            console.log('================================================================');
            console.log(`  Environment: ${NODE_ENV}`);
            console.log(`  API URL: http://localhost:${API_PORT}/api/v1`);
            console.log(`  Swagger UI: http://localhost:${API_PORT}/api/docs`);
            console.log(`  Health Check: http://localhost:${API_PORT}/api/v1/health`);
            if (NODE_ENV === 'production') {
                console.log(`  UI URL: http://localhost:${API_PORT}`);
            } else {
                console.log(`  UI URL: http://localhost:${UI_PORT} (dev server)`);
            }
            console.log('================================================================');
            console.log('');
        });
        
    } catch (error) {
        console.error('❌ Failed to start server:', error);
        process.exit(1);
    }
};

// Handle unhandled promise rejections
process.on('unhandledRejection', (err) => {
    console.error('Unhandled Promise Rejection:', err);
    process.exit(1);
});

// Handle uncaught exceptions
process.on('uncaughtException', (err) => {
    console.error('Uncaught Exception:', err);
    process.exit(1);
});

// Graceful shutdown
process.on('SIGTERM', () => {
    console.log('SIGTERM signal received: closing HTTP server');
    process.exit(0);
});

process.on('SIGINT', () => {
    console.log('SIGINT signal received: closing HTTP server');
    process.exit(0);
});

// Start the server
startServer();

module.exports = app;
