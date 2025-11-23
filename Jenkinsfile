// Jenkinsfile - Pipeline for the Real-Time Chat App

pipeline {
    agent any 

    environment {
        // Define common variables for the project
        IMAGE_NAME = 'chat-app' 
        DOCKER_REGISTRY = 'yourusername/chat-app' // REPLACE with your Docker Hub username!
    }

    stages {
        // Stage 1: Checkout (Pull) the code from GitHub
        stage('Checkout Code') {
            steps {
                git branch: 'main', url: 'https://github.com/yourusername/pj1.git' // REPLACE with your GitHub repo URL
            }
        }

        // Stage 2: Build the Docker Image
        stage('Build Image') {
            steps {
                // Build the image and tag it with the Jenkins Build Number
                script {
                    def customTag = "build-${env.BUILD_NUMBER}"
                    sh "docker build -t ${DOCKER_REGISTRY}:${customTag} ."
                    env.IMAGE_TAG = customTag // Store the tag for the next stage
                }
            }
        }

        // Stage 3: Push Image to Docker Hub (or other registry)
        stage('Push Image') {
            steps {
                // Requires Jenkins credentials to be set up for Docker Hub
                sh "docker push ${DOCKER_REGISTRY}:${IMAGE_TAG}"
            }
        }

        // Stage 4: Deploy the New Image (Stopping old and starting new)
        stage('Deploy Containers') {
            steps {
                // Stops and removes the old running containers gracefully
                sh 'docker compose down' 
                
                // Starts the new containers, pulling the new image tag if available
                // NOTE: In production, you would use Kubernetes/Terraform here. 
                // For this project, we use docker compose to start the new stack.
                sh 'docker compose up -d' 
            }
        }
    }
}