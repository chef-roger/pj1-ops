// Jenkinsfile - Pipeline for the Real-Time Chat App

pipeline {
    agent any

    environment {
        // Define common variables for the project
        IMAGE_NAME = 'chat-app'
        DOCKER_REGISTRY = 'steziwara/chat-app'
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
                // *** SYNTAX FIX: WRAP docker.withRegistry IN A 'script' BLOCK ***
                script {
                    // This wrapper handles logging in to Docker Hub using the stored Jenkins credentials (PAT)
                    docker.withRegistry("https://registry.hub.docker.com", DOCKER_CREDENTIALS_ID) {
                        sh "docker push ${DOCKER_REGISTRY}:${IMAGE_TAG}"
                    }
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
