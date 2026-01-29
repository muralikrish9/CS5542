Cybersecurity Knowledge Base - RAG Dataset
==========================================

Overview
--------
This dataset contains 12 comprehensive text files covering various cybersecurity and offensive security topics. The corpus is designed for Advanced RAG (Retrieval-Augmented Generation) systems testing and evaluation.

Total Size: ~116 KB
File Count: 12 text files
Content Type: Technical cybersecurity documentation
Domain: Offensive Security, Network Security, AI Security

File Descriptions
-----------------

1. penetration_testing_methodology.txt (4.9 KB)
   - Penetration testing phases and frameworks
   - PTES, OWASP, NIST methodologies
   - Tools and ethical considerations

2. adversarial_attacks_ai.txt (6.2 KB)
   - Adversarial machine learning concepts
   - White-box and black-box attacks
   - Attacks on LLMs and defense mechanisms

3. 5g_network_security.txt (6.9 KB)
   - 5G network architecture and security
   - Protocol vulnerabilities
   - Network slicing security

4. web_application_security.txt (8.4 KB)
   - OWASP Top 10 vulnerabilities
   - Web application testing methodologies
   - API security

5. cryptography_fundamentals.txt (8.0 KB)
   - Symmetric and asymmetric encryption
   - Hash functions and digital signatures
   - Cryptographic protocols (TLS, PKI)

6. incident_response_forensics.txt (8.7 KB)
   - Incident response framework
   - Digital forensics methodology
   - Memory and disk forensics

7. cloud_security.txt (9.2 KB)
   - Cloud service models (IaaS, PaaS, SaaS)
   - Shared responsibility model
   - Container and serverless security

8. social_engineering.txt (9.5 KB)
   - Social engineering attack types
   - Psychological principles exploited
   - Defense strategies and training

9. wireless_security.txt (9.8 KB)
   - 802.11 standards and protocols
   - Wireless attack vectors
   - Enterprise wireless security

10. malware_analysis.txt (11 KB)
    - Static and dynamic analysis techniques
    - Reverse engineering tools
    - Malware classification and types

11. exploit_development.txt (11 KB)
    - Memory corruption vulnerabilities
    - Exploitation techniques (ROP, heap exploits)
    - Security mitigations and bypasses

12. threat_intelligence.txt (11 KB)
    - Threat intelligence lifecycle
    - Threat actor profiling
    - Intelligence sources and platforms

13. devsecops_automation.txt (11 KB)
    - CI/CD pipeline security
    - Security automation tools
    - DevSecOps best practices

Dataset Characteristics
-----------------------
- Domain-specific terminology for testing semantic vs keyword search
- Hierarchical structure (headings, sections) for chunking strategy evaluation
- Cross-references between documents for testing retrieval accuracy
- Technical depth suitable for professional/academic contexts
- Mix of conceptual explanations and practical implementations

Recommended Query Examples
---------------------------

Normal Queries:
Q1: "What are the main phases of penetration testing?"
   - Expected sources: penetration_testing_methodology.txt
   - Keywords: reconnaissance, scanning, exploitation, reporting

Q2: "How does Return-Oriented Programming (ROP) work?"
   - Expected sources: exploit_development.txt
   - Keywords: ROP, gadgets, DEP bypass

Q3: "What security protocols are used in 5G networks?"
   - Expected sources: 5g_network_security.txt
   - Keywords: 5G-AKA, encryption, authentication

Ambiguous/Edge-Case Query:
Q4: "How can machine learning be used in security?"
   - Expected sources: adversarial_attacks_ai.txt, malware_analysis.txt, threat_intelligence.txt
   - Tests: cross-document retrieval, semantic understanding

Q5: "What are the best practices for cloud security?"
   - Expected sources: cloud_security.txt, devsecops_automation.txt
   - Tests: multi-source synthesis, policy vs technical details

Use Cases
---------
1. Hybrid search evaluation (BM25 vs vector embeddings)
2. Semantic chunking comparison
3. Re-ranking effectiveness testing
4. Cross-encoder performance analysis
5. Grounded answer generation with citations
6. Faithfulness and hallucination detection

Technical Notes
---------------
- All files are plain text format (.txt)
- UTF-8 encoding
- Approximately 5-10 pages of content when combined
- Suitable for sentence-transformers embeddings
- Contains technical terminology that benefits from domain-specific models

Author: Generated for CS 5542 Lab 2 - Advanced RAG Systems
Date: January 29, 2026
Version: 1.0
