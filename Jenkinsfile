// Jenkinsfile - Pipeline for the Real-Time Chat App

pipeline {
    // Uses the simplest agent type for maximum compatibility
    agent any

    environment {
        // Define common variables for the project
        IMAGE_NAME = 'chat-app'
        DOCKER_REGISTRY = 'steziwara/chat-app'
        // Credential ID must match what is set in Jenkins (ID: dockerhub-credentials)
        DOCKER_CREDENTIALS_ID = 'dockerhub-credentials' 
    }

    stages {
        // Stage 1: Checkout (Pull) the code from GitHub
        stage('Checkout Code') {
            steps {
                git branch: 'main', url: 'https://github.com/chef-roger/pj1-ops.git'
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
                // FINAL FIX: This block securely pulls credentials and performs a reliable
                // shell-based Docker login/push/logout sequence.
                withCredentials([usernamePassword(credentialsId: DOCKER_CREDENTIALS_ID, usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh "docker login -u ${DOCKER_USER} -p ${DOCKER_PASS} docker.io"
                    sh "docker push ${DOCKER_REGISTRY}:${IMAGE_TAG}"
                    sh "docker logout"
                }
            }
        }

        // Stage 4: Deploy the New Image (Stopping old and starting new)
        stage('Deploy Containers') {
            steps {
                // Stops and removes the old running containers gracefully
                sh 'docker compose down'

                // Starts the new containers, pulling the new image tag if available
                sh 'docker compose up -d'
            }
        }
    }
}
