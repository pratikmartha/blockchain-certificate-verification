// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title CertificateVerification
 * @dev Smart Contract for issuing and verifying academic & professional certificates
 *      on the Ethereum blockchain, providing tamper-proof authenticity and transparency.
 */
contract CertificateVerification {

    // Owner of the smart contract (deploying institution/admin)
    address public owner;

    // Structure defining a digital certificate on-chain
    struct Certificate {
        string certificateId;
        string studentName;
        string course;
        string institution;
        string certificateHash; // Cryptographic SHA-256 hash of certificate payload
        uint256 issueDate;       // Blockchain block timestamp
        bool exists;
    }

    // Mapping from unique Certificate ID to Certificate data
    mapping(string => Certificate) public certificates;

    // Array storing all issued certificate IDs for public ledger enumeration
    string[] public certificateList;

    // Event emitted when a certificate is anchored onto the blockchain
    event CertificateIssued(
        string indexed certificateId,
        string studentName,
        string institution,
        string certificateHash,
        uint256 issueDate,
        address indexed issuer
    );

    // Modifier to restrict actions to contract owner
    modifier onlyOwner() {
        require(msg.sender == owner, "Only contract owner can execute this");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    /**
     * @notice Issue a new certificate on the blockchain
     * @param _certificateId Unique identifier for the certificate
     * @param _studentName Name of the recipient
     * @param _course Course or qualification earned
     * @param _institution Issuing organization or university
     * @param _certificateHash Cryptographic SHA-256 digest of the certificate
     */
    function issueCertificate(
        string memory _certificateId,
        string memory _studentName,
        string memory _course,
        string memory _institution,
        string memory _certificateHash
    ) public {
        require(bytes(_certificateId).length > 0, "Certificate ID cannot be empty");
        require(bytes(_studentName).length > 0, "Student name cannot be empty");
        require(bytes(_certificateHash).length > 0, "Certificate hash cannot be empty");
        require(!certificates[_certificateId].exists, "Certificate already exists with this ID");

        // Record the certificate permanently on the blockchain
        certificates[_certificateId] = Certificate({
            certificateId: _certificateId,
            studentName: _studentName,
            course: _course,
            institution: _institution,
            certificateHash: _certificateHash,
            issueDate: block.timestamp,
            exists: true
        });

        certificateList.push(_certificateId);

        emit CertificateIssued(
            _certificateId,
            _studentName,
            _institution,
            _certificateHash,
            block.timestamp,
            msg.sender
        );
    }

    /**
     * @notice Verify a certificate by its unique ID
     * @param _certificateId The ID to look up
     * @return certificateId The certificate ID
     * @return studentName The recipient's name
     * @return course The course/degree
     * @return institution The issuing institution
     * @return certificateHash The SHA-256 cryptographic hash recorded on-chain
     * @return issueDate Unix timestamp of issuance
     * @return exists Boolean flag indicating whether the certificate is genuine and exists
     */
    function verifyCertificate(
        string memory _certificateId
    )
        public
        view
        returns (
            string memory,
            string memory,
            string memory,
            string memory,
            string memory,
            uint256,
            bool
        )
    {
        Certificate memory cert = certificates[_certificateId];

        return (
            cert.certificateId,
            cert.studentName,
            cert.course,
            cert.institution,
            cert.certificateHash,
            cert.issueDate,
            cert.exists
        );
    }

    /**
     * @notice Get total count of certificates issued on the blockchain
     */
    function getTotalCertificates() public view returns (uint256) {
        return certificateList.length;
    }

    /**
     * @notice Fetch certificate ID at a specific index from the public ledger
     */
    function getCertificateIdByIndex(uint256 _index) public view returns (string memory) {
        require(_index < certificateList.length, "Index out of range");
        return certificateList[_index];
    }
}