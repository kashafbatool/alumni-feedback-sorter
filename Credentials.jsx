import { motion } from 'framer-motion';
import { fadeInUpScroll } from '../../utils/animations';
import styles from './Credentials.module.css';

const Credentials = () => {
  const credentials = [
    {
      title: "Full Stack Development",
      description: "Proficient in React, Node.js, Express, and MongoDB. Building complete web applications from concept to deployment."
    },
    {
      title: "UI/UX Design",
      description: "Creating intuitive, accessible interfaces with modern design principles. Experience with Figma and user research."
    },
    {
      title: "Cloud & DevOps",
      description: "Deploying and managing applications on AWS, Docker, and CI/CD pipelines. Experience with automation and scaling."
    },
    {
      title: "Problem Solving",
      description: "Strong algorithmic thinking and data structures knowledge. Competitive programming experience and code optimization."
    }
  ];

  return (
    <section id="credentials" className={styles.credentials}>
      <motion.h2 
        {...fadeInUpScroll}
        className={styles.title}
      >
        Skills & Expertise
      </motion.h2>
      <div className={styles.grid}>
        {credentials.map((cred, index) => (
          <motion.div
            key={index}
            className={styles.card}
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.3 }}
            transition={{ duration: 0.5, delay: index * 0.1 }}
            whileHover={{ y: -10, boxShadow: "0 20px 30px rgba(0,0,0,0.1)" }}
          >
            <h3>{cred.title}</h3>
            <p>{cred.description}</p>
          </motion.div>
        ))}
      </div>
    </section>
  );
};

export default Credentials;
