/**
 * Authentication Routes
 */

const express = require('express');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const { asyncHandler } = require('../middleware/errorHandler');
const { validateRequired } = require('../middleware/validator');

const router = express.Router();

const JWT_SECRET = process.env.JWT_SECRET || 'fincore_jwt_secret_2024';
const JWT_EXPIRES_IN = process.env.JWT_EXPIRES_IN || '24h';

// Hardcoded users for training purposes
const USERS = [
    {
        id: 1,
        username: 'admin',
        password: '$2b$10$rZ5qXVYYZ5YYZ5YYZ5YYZeO5YYZ5YYZ5YYZ5YYZ5YYZ5YYZ5YYZ5Y', // Admin@123
        role: 'admin'
    },
    {
        id: 2,
        username: 'viewer',
        password: '$2b$10$vZ5qXVYYZ5YYZ5YYZ5YYZeO5YYZ5YYZ5YYZ5YYZ5YYZ5YYZ5YYZ5Y', // Viewer@123
        role: 'read_only'
    },
    {
        id: 3,
        username: 'testuser',
        password: '$2b$10$tZ5qXVYYZ5YYZ5YYZ5YYZeO5YYZ5YYZ5YYZ5YYZ5YYZ5YYZ5YYZ5Y', // Test@123
        role: 'standard'
    }
];

// Pre-hash passwords on startup (for demo purposes)
const initializeUsers = () => {
    USERS[0].password = bcrypt.hashSync('Admin@123', 10);
    USERS[1].password = bcrypt.hashSync('Viewer@123', 10);
    USERS[2].password = bcrypt.hashSync('Test@123', 10);
};
initializeUsers();

/**
 * @swagger
 * /auth/login:
 *   post:
 *     summary: User login
 *     tags: [Authentication]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - username
 *               - password
 *             properties:
 *               username:
 *                 type: string
 *                 example: admin
 *               password:
 *                 type: string
 *                 example: Admin@123
 *     responses:
 *       200:
 *         description: Login successful
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 token:
 *                   type: string
 *                   description: JWT token
 *                 user:
 *                   type: object
 *                   properties:
 *                     id:
 *                       type: integer
 *                     username:
 *                       type: string
 *                     role:
 *                       type: string
 *                 expires_in:
 *                   type: string
 *                   example: 24h
 *       401:
 *         description: Invalid credentials
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 */
router.post('/login', 
    validateRequired(['username', 'password']),
    asyncHandler(async (req, res) => {
        const { username, password } = req.body;
        
        // Find user
        const user = USERS.find(u => u.username === username);
        
        if (!user) {
            return res.status(401).json({
                error: 'Invalid username or password',
                code: 'AUTH_INVALID_CREDENTIALS'
            });
        }
        
        // Verify password
        const validPassword = await bcrypt.compare(password, user.password);
        
        if (!validPassword) {
            return res.status(401).json({
                error: 'Invalid username or password',
                code: 'AUTH_INVALID_CREDENTIALS'
            });
        }
        
        // Generate JWT token
        const token = jwt.sign(
            {
                id: user.id,
                username: user.username,
                role: user.role
            },
            JWT_SECRET,
            { expiresIn: JWT_EXPIRES_IN }
        );
        
        res.json({
            token,
            user: {
                id: user.id,
                username: user.username,
                role: user.role
            },
            expires_in: JWT_EXPIRES_IN
        });
    })
);

/**
 * @swagger
 * /auth/verify:
 *   get:
 *     summary: Verify JWT token
 *     tags: [Authentication]
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       200:
 *         description: Token is valid
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 valid:
 *                   type: boolean
 *                 user:
 *                   type: object
 *       401:
 *         description: Invalid or expired token
 */
router.get('/verify', asyncHandler(async (req, res) => {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];
    
    if (!token) {
        return res.status(401).json({
            error: 'Token required',
            code: 'TOKEN_REQUIRED'
        });
    }
    
    try {
        const decoded = jwt.verify(token, JWT_SECRET);
        res.json({
            valid: true,
            user: {
                id: decoded.id,
                username: decoded.username,
                role: decoded.role
            }
        });
    } catch (err) {
        res.status(401).json({
            error: 'Invalid or expired token',
            code: 'INVALID_TOKEN'
        });
    }
}));

module.exports = router;
