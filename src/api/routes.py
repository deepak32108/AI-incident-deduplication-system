from flask import Flask, request, jsonify
from src.models.incident import Incident, IncidentStatus, SeverityLevel
from src.embeddings.embedding_service import EmbeddingService
from src.vector_db.vector_store import VectorStore
from src.deduplication.deduplication_engine import DeduplicationEngine
from src.rag.rag_pipeline import RAGPipeline
from config import config
from datetime import datetime
import logging

logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize services
try:
    embedding_service = EmbeddingService()
    vector_store = VectorStore()
    dedup_engine = DeduplicationEngine(embedding_service, vector_store)
    rag_pipeline = RAGPipeline()
    logger.info("All services initialized successfully")
except Exception as e:
    logger.error(f"Initialization error: {e}")
    raise

incidents_db = {}


# ============ HEALTH & STATUS ============

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'vector_store_size': vector_store.get_index_size(),
        'total_incidents': len(incidents_db),
        'timestamp': datetime.now().isoformat()
    }), 200


# ============ CREATE INCIDENTS ============

@app.route('/api/incidents', methods=['POST'])
def create_incident():
    """Create incident"""
    try:
        data = request.json

        if not all(k in data for k in ['title', 'description', 'severity', 'source']):
            return jsonify({'error': 'Missing required fields'}), 400

        new_incident = Incident(
            title=data['title'],
            description=data['description'],
            severity=SeverityLevel[data['severity'].upper()],
            source=data['source']
        )

        existing_incidents = list(incidents_db.values())
        is_duplicate, parent_incident, score = dedup_engine.deduplicate(
            new_incident, existing_incidents
        )

        if is_duplicate and parent_incident:
            dedup_engine.mark_as_duplicate(new_incident, parent_incident)
            rag_analysis = rag_pipeline.analyze_duplicate_incidents(
                new_incident, [parent_incident], score
            )
            incidents_db[new_incident.id] = new_incident

            return jsonify({
                'id': new_incident.id,
                'status': new_incident.status.value,
                'is_duplicate': True,
                'duplicate_of': parent_incident.id,
                'similarity_score': float(score),
                'rag_analysis': rag_analysis
            }), 201

        dedup_engine.index_incident(new_incident)
        incidents_db[new_incident.id] = new_incident

        logger.info(f"Created incident: {new_incident.id}")
        return jsonify({
            'id': new_incident.id,
            'status': new_incident.status.value,
            'is_duplicate': False
        }), 201

    except KeyError:
        return jsonify({'error': 'Invalid severity. Use: critical, high, medium, low'}), 400
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({'error': str(e)}), 500


# ============ RETRIEVE INCIDENTS ============

@app.route('/api/incidents/<incident_id>', methods=['GET'])
def get_incident(incident_id):
    """Get incident"""
    incident = incidents_db.get(incident_id)
    if not incident:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(incident.to_dict()), 200


@app.route('/api/incidents', methods=['GET'])
def list_incidents():
    """List incidents"""
    incidents = [inc.to_dict() for inc in incidents_db.values()]
    return jsonify({'total': len(incidents), 'incidents': incidents}), 200


# ============ SEARCH INCIDENTS ============

@app.route('/api/incidents/search', methods=['GET'])
def search_incidents():
    """Search incidents by query"""
    try:
        query = request.args.get('q', '').lower()

        if not query:
            return jsonify({'error': 'Query required'}), 400

        results = []
        for incident in incidents_db.values():
            if (query in incident.title.lower() or
                query in incident.description.lower() or
                query in incident.source.lower()):
                results.append(incident.to_dict())

        return jsonify({'total': len(results), 'results': results}), 200
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({'error': str(e)}), 500


# ============ RESOLVE/CLOSE INCIDENTS ============

@app.route('/api/incidents/<incident_id>/resolve', methods=['POST'])
def resolve_incident(incident_id):
    """Resolve incident"""
    try:
        incident = incidents_db.get(incident_id)
        if not incident:
            return jsonify({'error': 'Not found'}), 404

        similar_incidents = [inc for inc in incidents_db.values()
                             if inc.status == IncidentStatus.RESOLVED]
        resolution = rag_pipeline.generate_resolution(incident, similar_incidents)

        incident.status = IncidentStatus.RESOLVED
        incident.resolved_at = datetime.now()
        incident.resolution_notes = resolution

        return jsonify({
            'id': incident.id,
            'status': incident.status.value,
            'resolution': resolution
        }), 200
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/incidents/<incident_id>/close', methods=['POST'])
def close_incident(incident_id):
    """Close incident"""
    try:
        incident = incidents_db.get(incident_id)
        if not incident:
            return jsonify({'error': 'Not found'}), 404

        if incident.status != IncidentStatus.RESOLVED:
            return jsonify({'error': 'Must be resolved first'}), 400

        incident.status = IncidentStatus.CLOSED
        incident.closed_at = datetime.now()

        return jsonify({'id': incident.id, 'status': incident.status.value}), 200
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({'error': str(e)}), 500


# ============ STATISTICS ============

@app.route('/api/incidents/stats', methods=['GET'])
def get_stats():
    """Get statistics"""
    total = len(incidents_db)
    duplicates = sum(1 for inc in incidents_db.values() if inc.status == IncidentStatus.DUPLICATE)
    resolved = sum(1 for inc in incidents_db.values() if inc.status == IncidentStatus.RESOLVED)
    closed = sum(1 for inc in incidents_db.values() if inc.status == IncidentStatus.CLOSED)
    open_incidents = sum(1 for inc in incidents_db.values() if inc.status == IncidentStatus.OPEN)

    return jsonify({
        'total_incidents': total,
        'open_incidents': open_incidents,
        'duplicate_count': duplicates,
        'resolved_count': resolved,
        'closed_count': closed,
        'deduplication_rate': (duplicates / total * 100) if total > 0 else 0,
        'resolution_rate': ((resolved + closed) / total * 100) if total > 0 else 0
    }), 200


# ============ BULK OPERATIONS ============

@app.route('/api/incidents/bulk', methods=['POST'])
def bulk_create_incidents():
    """Bulk create incidents"""
    try:
        data = request.json
        incidents_data = data.get('incidents', [])

        results = []
        for inc_data in incidents_data:
            try:
                incident = Incident(
                    title=inc_data['title'],
                    description=inc_data['description'],
                    severity=SeverityLevel[inc_data['severity'].upper()],
                    source=inc_data['source']
                )

                existing = list(incidents_db.values())
                is_dup, parent, score = dedup_engine.deduplicate(incident, existing)

                if is_dup and parent:
                    dedup_engine.mark_as_duplicate(incident, parent)
                    incidents_db[incident.id] = incident
                    results.append({'id': incident.id, 'status': 'duplicate', 'duplicate_of': parent.id})
                else:
                    dedup_engine.index_incident(incident)
                    incidents_db[incident.id] = incident
                    results.append({'id': incident.id, 'status': 'created'})
            except Exception as e:
                logger.error(f"Error in bulk create: {e}")
                results.append({'status': 'error', 'message': str(e)})

        return jsonify({'total': len(results), 'results': results}), 201

    except Exception as e:
        logger.error(f"Bulk create error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/incidents/resolve-batch', methods=['POST'])
def batch_resolve():
    """Resolve multiple incidents"""
    try:
        data = request.json
        incident_ids = data.get('incident_ids', [])

        results = []
        for inc_id in incident_ids:
            incident = incidents_db.get(inc_id)
            if incident:
                incident.status = IncidentStatus.RESOLVED
                incident.resolved_at = datetime.now()
                results.append({'id': inc_id, 'status': 'resolved'})
            else:
                results.append({'id': inc_id, 'status': 'not_found'})

        return jsonify({'total': len(results), 'results': results}), 200
    except Exception as e:
        logger.error(f"Batch resolve error: {e}")
        return jsonify({'error': str(e)}), 500


# ============ EXPORT/IMPORT ============

@app.route('/api/incidents/export', methods=['GET'])
def export_incidents():
    """Export all incidents as JSON"""
    try:
        incidents = [inc.to_dict() for inc in incidents_db.values()]

        response = jsonify({
            'total': len(incidents),
            'exported_at': datetime.now().isoformat(),
            'incidents': incidents
        })
        response.headers['Content-Disposition'] = 'attachment; filename=incidents.json'
        return response, 200
    except Exception as e:
        logger.error(f"Export error: {e}")
        return jsonify({'error': str(e)}), 500


# ============ CLEAR DATA ============

@app.route('/api/incidents/clear', methods=['DELETE'])
def clear_incidents():
    """Clear all incidents (be careful!)"""
    try:
        global incidents_db
        count = len(incidents_db)
        incidents_db.clear()
        vector_store.clear()
        logger.warning(f"Cleared {count} incidents")
        return jsonify({'message': f'Cleared {count} incidents'}), 200
    except Exception as e:
        logger.error(f"Clear error: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)