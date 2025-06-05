const { models } = require('../models');
const bcrypt = require('bcryptjs');

/**
 * User Service - Handles business logic for user-related operations
 */
class UserService {
  /**
   * Get a user by ID
   * 
   * @param {string} id - User ID
   * @returns {Promise<Object|null>} User object or null if not found
   */
  async getUserById(id) {
    try {
      // For demo, using the existing Python models
      const user = models.User.get_by_id(id);
      
      if (!user) {
        return null;
      }
      
      return {
        id: user.id,
        username: user.username,
        email: user.email,
        password_hash: user.password_hash
      };
    } catch (error) {
      console.error('Error getting user by ID:', error);
      throw error;
    }
  }
  
  /**
   * Get a user by username
   * 
   * @param {string} username - Username to look up
   * @returns {Promise<Object|null>} User object or null if not found
   */
  async getUserByUsername(username) {
    try {
      // For demo, using the existing Python models
      const user = models.User.get_by_username(username);
      
      if (!user) {
        return null;
      }
      
      return {
        id: user.id,
        username: user.username,
        email: user.email,
        password_hash: user.password_hash
      };
    } catch (error) {
      console.error('Error getting user by username:', error);
      throw error;
    }
  }
  
  /**
   * Create a new user
   * 
   * @param {Object} userData - User data object
   * @returns {Promise<Object>} New user object
   */
  async createUser(userData) {
    try {
      const { username, email, password } = userData;
      
      // Check if username already exists
      const existingUser = await this.getUserByUsername(username);
      if (existingUser) {
        throw new Error('Username already exists');
      }
      
      // Hash password
      const salt = await bcrypt.genSalt(10);
      const hashedPassword = await bcrypt.hash(password, salt);
      
      // Create user in database
      // In a real implementation, this would use an ORM like Sequelize
      // For demo, this would create a new user in the Python models
      
      // Return new user (mock)
      return {
        id: 'new-user-id',
        username,
        email,
        password_hash: hashedPassword
      };
    } catch (error) {
      console.error('Error creating user:', error);
      throw error;
    }
  }
}

module.exports = new UserService();