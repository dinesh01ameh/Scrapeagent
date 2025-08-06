# SwissKnife AI Scraper - Development Rules & Standards

## 🚨 **PERMANENT DEVELOPMENT RULES**

This document establishes **MANDATORY** rules and standards for the SwissKnife AI Scraper project. These rules are **NON-NEGOTIABLE** and must be followed by all team members, contributors, and automated systems.

**Status:** ✅ **OFFICIAL STANDARD**  
**Enforcement:** **MANDATORY**  
**Last Updated:** August 6, 2025

---

## 🌐 **RULE #1: PORT CONFIGURATION (CRITICAL)**

### **PERMANENT PORT MAPPING**
These ports are **HARDCODED** and **MUST NOT BE CHANGED**:

- **Frontend (Smart Scraper AI)**: `http://localhost:8650` 🔒
- **Backend API**: `http://localhost:8601` 🔒
- **Crawl4AI Service**: `http://localhost:11235` 🔒
- **PostgreSQL Database**: `localhost:5434` 🔒
- **Redis Cache**: `localhost:6379` 🔒
- **Ollama LLM**: `localhost:11435` 🔒

### **ENFORCEMENT RULES**
1. **ALL browser automation tests MUST use port 8650**
2. **ALL API calls MUST target port 8601**
3. **ALL documentation MUST reference these ports**
4. **ALL configuration files MUST use these ports**
5. **NO exceptions without full team approval and documentation update**

### **VIOLATION CONSEQUENCES**
- ❌ **Immediate test failures**
- ❌ **Broken development environment**
- ❌ **Production deployment issues**
- ❌ **Team confusion and wasted time**

---

## 🔐 **RULE #2: AUTHENTICATION SYSTEM INTEGRITY**

### **PROTECTED COMPONENTS**
The following authentication components are **PRODUCTION-CRITICAL** and require special approval for changes:

1. **JWT Token Management**: Token generation, storage, and validation
2. **Password Security**: Hashing, validation, and storage
3. **Session Management**: Authentication state and persistence
4. **Protected Routes**: Route protection and access control
5. **API Security**: CORS, validation, and error handling

### **CHANGE APPROVAL PROCESS**
1. **Security Review**: All authentication changes require security review
2. **Testing Requirement**: 100% test coverage for authentication changes
3. **Documentation Update**: All changes must update relevant documentation
4. **Rollback Plan**: All changes must include rollback procedures

---

## 🏗️ **RULE #3: ARCHITECTURAL COMPLIANCE**

### **CORE TECHNOLOGY STACK (IMMUTABLE)**
These technologies are **FOUNDATIONAL** and cannot be replaced:

1. **Crawl4AI Docker Service**: PRIMARY scraping engine
2. **Jina AI APIs**: CORE AI processing engine
3. **FastAPI Backend**: Main API framework
4. **React Frontend**: User interface framework
5. **PostgreSQL**: Primary database
6. **Redis**: Cache and session storage

### **INTEGRATION REQUIREMENTS**
- **ALL scraping operations MUST use Crawl4AI**
- **ALL AI processing MUST use Jina AI APIs**
- **NO custom scraping engines without approval**
- **NO alternative AI services without justification**

---

## 🧪 **RULE #4: TESTING STANDARDS**

### **MANDATORY TESTING REQUIREMENTS**
1. **Authentication Flow**: 100% coverage required
2. **API Endpoints**: All endpoints must have tests
3. **Frontend Components**: Critical components must be tested
4. **Integration Tests**: End-to-end scenarios required
5. **Browser Automation**: Playwright tests for user flows

### **TESTING RULES**
- **ALL tests MUST use correct port configuration**
- **ALL authentication tests MUST cover edge cases**
- **ALL API tests MUST validate error handling**
- **ALL browser tests MUST use port 8650**
- **NO production deployment without passing tests**

---

## 📝 **RULE #5: CODE QUALITY STANDARDS**

### **FORMATTING & LINTING**
1. **Frontend**: ESLint + Prettier configuration must be followed
2. **Backend**: Black + isort + flake8 for Python code
3. **TypeScript**: Strict type checking enabled
4. **Imports**: Relative imports preferred over absolute paths
5. **Comments**: Critical functions must be documented

### **CODE REVIEW REQUIREMENTS**
- **ALL authentication changes require review**
- **ALL port configuration changes require review**
- **ALL architectural changes require review**
- **ALL security-related changes require review**

---

## 🚀 **RULE #6: DEPLOYMENT STANDARDS**

### **ENVIRONMENT CONSISTENCY**
1. **Development**: Must match production configuration
2. **Testing**: Must use same ports and services
3. **Staging**: Must mirror production exactly
4. **Production**: Must follow all established standards

### **DEPLOYMENT CHECKLIST**
- ✅ **Port configuration verified**
- ✅ **Authentication system tested**
- ✅ **All services operational**
- ✅ **Database migrations applied**
- ✅ **Environment variables configured**
- ✅ **Health checks passing**

---

## 📚 **RULE #7: DOCUMENTATION MAINTENANCE**

### **MANDATORY DOCUMENTATION UPDATES**
When making changes, the following documents **MUST** be updated:

1. **PORT_CONFIGURATION.md**: For any port-related changes
2. **AUTHENTICATION_SYSTEM.md**: For authentication changes
3. **CHANGELOG.md**: For all significant changes
4. **project_status.md**: For milestone updates
5. **README.md**: For access URL changes

### **DOCUMENTATION STANDARDS**
- **ALL changes must be documented immediately**
- **ALL documentation must be accurate and current**
- **ALL examples must use correct port numbers**
- **ALL links must be functional and up-to-date**

---

## 🔍 **RULE #8: TROUBLESHOOTING PROTOCOLS**

### **COMMON ISSUES & SOLUTIONS**

#### **Port-Related Issues**
1. **Problem**: Browser tests failing
   - **Solution**: Verify using `http://localhost:8650`
   - **Check**: `docker ps` for correct port mapping

2. **Problem**: API calls failing
   - **Solution**: Verify using `http://localhost:8601`
   - **Check**: Backend container health status

#### **Authentication Issues**
1. **Problem**: Login not working
   - **Solution**: Check JWT token generation and storage
   - **Check**: API endpoint responses and error messages

2. **Problem**: Protected routes not working
   - **Solution**: Verify authentication state management
   - **Check**: Token validation and expiration

---

## ⚠️ **RULE #9: EMERGENCY PROCEDURES**

### **CRITICAL SYSTEM FAILURE**
1. **Immediate Actions**:
   - Check all container health status
   - Verify port accessibility
   - Review recent changes in git history
   - Check authentication system status

2. **Recovery Steps**:
   - Restart Docker containers if needed
   - Verify database connectivity
   - Test authentication flow
   - Validate all service endpoints

### **ROLLBACK PROCEDURES**
- **ALL changes must be reversible**
- **ALL deployments must have rollback plans**
- **ALL database changes must be backward compatible**
- **ALL configuration changes must be documented**

---

## 🎯 **RULE #10: COMPLIANCE MONITORING**

### **AUTOMATED CHECKS**
1. **Port Configuration**: Automated verification in CI/CD
2. **Authentication Tests**: Mandatory in all pipelines
3. **Code Quality**: Linting and formatting checks
4. **Documentation**: Link validation and accuracy checks

### **MANUAL REVIEWS**
1. **Weekly**: Port configuration verification
2. **Monthly**: Authentication system audit
3. **Quarterly**: Full architectural compliance review
4. **Annually**: Security assessment and updates

---

## 📞 **RULE ENFORCEMENT & SUPPORT**

### **VIOLATION REPORTING**
- **Immediate**: Report critical violations (port changes, auth issues)
- **Weekly**: Report minor violations (documentation, formatting)
- **Monthly**: Review compliance metrics and improvements

### **SUPPORT CHANNELS**
- **Technical Issues**: Check health endpoints and logs
- **Rule Clarification**: Refer to this document and related docs
- **Emergency Support**: Follow emergency procedures above

---

## 🏆 **SUCCESS METRICS**

### **COMPLIANCE TARGETS**
- **Port Configuration**: 100% compliance
- **Authentication System**: 100% uptime
- **Test Coverage**: 95%+ for critical components
- **Documentation**: 100% accuracy
- **Code Quality**: Zero critical violations

---

**These rules ensure the continued success, security, and maintainability of the SwissKnife AI Scraper project. Compliance is mandatory for all team members and automated systems.**
