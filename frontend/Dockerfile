FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json ./

RUN npm install

# Copy the rest of the application code is not strictly needed if volumes are mounted, 
# but good for the image build layer.
COPY . .

# Expose Vite port
EXPOSE 5173

# Start development server with host binding
CMD ["npm", "run", "dev", "--", "--host"]
